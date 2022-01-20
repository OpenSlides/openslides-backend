from importlib import import_module
from typing import Any, Dict

import pytest
from datastore.migrations import MigrationHandler
from datastore.migrations.core.setup import register_services
from datastore.reader.core import GetRequest, Reader
from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.services import ReadDatabase
from datastore.shared.services.environment_service import (
    DATASTORE_DEV_MODE_ENVIRONMENT_VAR,
    EnvironmentService,
)
from datastore.shared.util import DeletedModelsBehaviour
from datastore.writer.core import Writer
from datastore.writer.flask_frontend.json_handlers import WriteHandler


@pytest.fixture(autouse=True)
def setup() -> None:
    register_services()
    env_service: EnvironmentService = injector.get(EnvironmentService)
    env_service.set(DATASTORE_DEV_MODE_ENVIRONMENT_VAR, "1")


@pytest.fixture(autouse=True)
def clear_datastore(setup) -> None:
    writer: Writer = injector.get(Writer)
    writer.truncate_db()

    def _clear_datastore() -> None:
        writer: Writer = injector.get(Writer)
        writer.truncate_db()

    return _clear_datastore


@pytest.fixture()
def write(clear_datastore) -> None:
    def _write(*events: Dict[str, Any]):
        payload = {
            "user_id": 1,
            "information": {},
            "locked_fields": {},
            "events": events,
        }
        write_handler = WriteHandler()
        write_handler.write(payload)

    yield _write


@pytest.fixture()
def migrate(clear_datastore):
    def _migrate(migration_module_name):
        migration_module = import_module(f"migrations.{migration_module_name}")

        class Migration(migration_module.Migration):
            target_migration_index = 2

        connection = injector.get(ConnectionHandler)
        with connection.get_connection_context():
            connection.execute("update positions set migration_index=%s", [1])

        migration_handler = injector.get(MigrationHandler)
        migration_handler.register_migrations(Migration)
        migration_handler.migrate()

    yield _migrate


@pytest.fixture()
def finalize(clear_datastore):
    def _finalize(migration_module_name):
        migration_module = import_module(f"migrations.{migration_module_name}")

        class Migration(migration_module.Migration):
            target_migration_index = 2

        connection = injector.get(ConnectionHandler)
        with connection.get_connection_context():
            connection.execute("update positions set migration_index=%s", [1])

        migration_handler = injector.get(MigrationHandler)
        migration_handler.register_migrations(Migration)
        migration_handler.finalize()

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
    def _assert_model(fqid, expected, position=None):
        if position is None:
            assert read_model(fqid) == expected

            # get max position
            read_database: ReadDatabase = injector.get(ReadDatabase)
            with read_database.get_context():
                position = read_database.get_max_position()

        # build model and check
        assert read_model(fqid, position=position) == expected

    yield _assert_model
