import json
from copy import deepcopy
from importlib import import_module
from typing import Any

import pytest
from datastore.migrations import MigrationHandler
from datastore.migrations.core.setup import register_services
from datastore.reader.core import GetEverythingRequest, GetRequest, Reader
from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.services import ReadDatabase
from datastore.shared.util import (
    DeletedModelsBehaviour,
    ModelDoesNotExist,
    strip_reserved_fields,
)
from datastore.writer.core import Writer
from datastore.writer.flask_frontend.json_handlers import WriteHandler

from openslides_backend.migrations import get_backend_migration_index
from openslides_backend.models.base import model_registry
from openslides_backend.models.checker import Checker


class DoesNotExist:
    """Marker class to check for the existence of a model."""


class MigrationChecker(Checker):
    """Adjusted Checker for migrations which is capable of handling dummy fields & collections."""

    def check_collections(self) -> None:
        pass

    def check_normal_fields(self, model: dict[str, Any], collection: str) -> bool:
        return False

    def check_types(self, *args, **kwargs) -> None:
        pass

    def check_relation(
        self, model: dict[str, Any], collection: str, field: str
    ) -> None:
        if collection not in model_registry or not self.get_model(
            collection
        ).try_get_field(field):
            return
        return super().check_relation(model, collection, field)


@pytest.fixture(autouse=True)
def setup() -> None:
    register_services()


@pytest.fixture(autouse=True)
def clear_datastore(setup) -> None:
    def _clear_datastore() -> None:
        writer: Writer = injector.get(Writer)
        writer.truncate_db()

    _clear_datastore()
    return _clear_datastore


@pytest.fixture()
def write(clear_datastore) -> None:
    def _write(*events: dict[str, Any]):
        payload = {
            "user_id": 1,
            "information": {},
            "locked_fields": {},
            "events": events,
        }
        write_handler = WriteHandler()
        write_handler.write(payload)

    yield _write


def setup_dummy_migration_handler(migration_module_name):
    migration_module = import_module(
        f"openslides_backend.migrations.migrations.{migration_module_name}"
    )

    class Migration(migration_module.Migration):
        target_migration_index = 2

    connection = injector.get(ConnectionHandler)
    with connection.get_connection_context():
        connection.execute("update positions set migration_index=%s", [1])

    migration_handler = injector.get(MigrationHandler)
    migration_handler.register_migrations(Migration)
    return migration_handler


@pytest.fixture()
def migrate(clear_datastore):
    def _migrate(migration_module_name):
        setup_dummy_migration_handler(migration_module_name).migrate()

    yield _migrate


@pytest.fixture()
def finalize(clear_datastore):
    def _finalize(migration_module_name):
        setup_dummy_migration_handler(migration_module_name).finalize()

        # check relations
        reader: Reader = injector.get(Reader)
        with reader.get_database_context():
            response = reader.get_everything(GetEverythingRequest())

        for models in response.values():
            for model in models.values():
                strip_reserved_fields(model)
        response["_migration_index"] = get_backend_migration_index()

        MigrationChecker(json.loads(json.dumps(response))).run_check()

    yield _finalize


@pytest.fixture()
def read_model(clear_datastore):
    def _read_model(fqid, position=None):
        reader: Reader = injector.get(Reader)
        with reader.get_database_context():
            request = GetRequest(
                fqid=fqid,
                position=position,
                get_deleted_models=DeletedModelsBehaviour.ALL_MODELS,
            )
            return reader.get(request)

    yield _read_model


@pytest.fixture()
def assert_model(read_model):
    def compare_models(model, expected):
        # fix order of lists
        for key, value in expected.items():
            if (
                key in model
                and isinstance(model[key], list)
                and isinstance(value, list)
                and sorted(model[key]) == sorted(value)
            ):
                expected[key] = model[key]
        assert model == expected

    def _assert_model(fqid, _expected, position=None):
        # try to fetch model and assert correct existance
        try:
            model = read_model(fqid, position=position)
        except ModelDoesNotExist:
            if not isinstance(_expected, DoesNotExist):
                raise
            else:
                return
        assert not isinstance(_expected, DoesNotExist)

        expected = deepcopy(_expected)
        if "meta_deleted" not in expected:
            expected["meta_deleted"] = False

        # don't compare meta_position if it's not requested
        if "meta_position" not in expected:
            expected["meta_position"] = model["meta_position"]

        if position is None:
            # assert that current model is equal to expected
            compare_models(model, expected)
            # get max position
            read_database: ReadDatabase = injector.get(ReadDatabase)
            with read_database.get_context():
                position = read_database.get_max_position()

            # additionally assert that the model at the max position is equal to expected
            model = read_model(fqid, position=position)

        compare_models(model, expected)

    yield _assert_model
