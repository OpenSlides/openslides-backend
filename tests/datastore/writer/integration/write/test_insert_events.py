import copy
from unittest.mock import MagicMock

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.services import (
    EnvironmentService,
    ReadDatabase,
)
from openslides_backend.datastore.shared.util import ModelDoesNotExist, ModelExists
from openslides_backend.datastore.writer.core import Database
from openslides_backend.datastore.writer.core import setup_di as core_setup_di
from openslides_backend.datastore.writer.flask_frontend.json_handlers import (
    WriteHandler,
)
from openslides_backend.datastore.writer.postgresql_backend import (
    EventTranslator,
    SqlDatabaseBackendService,
)
from openslides_backend.datastore.writer.postgresql_backend.event_translator import (
    EventTranslatorService,
)
from openslides_backend.shared.patterns import META_DELETED
from tests.datastore import reset_di  # noqa


class FakeConnectionHandler:
    def get_connection_context(self):
        return MagicMock()

    def execute(self, query, arguments, use_execute_values=False):
        return self._query(query, arguments, use_execute_values)

    def query_single_value(self, query, arguments):
        return self._query(query, arguments)

    def query_list_of_single_values(self, query, arguments, use_execute_values=False):
        return self._query(query, arguments, use_execute_values)

    def to_json(self, data):
        return data

    def _query(self, query, arguments, use_execute_values=False):
        if query.strip().startswith("insert into positions ("):
            return self._create_position(query, arguments)
        if query.strip().startswith("insert into models ("):
            return self._update_models(query, arguments)
        if query.strip().startswith("insert into id_sequences ("):
            return self._update_id_sequences(query, arguments)
        if query.strip().startswith("insert into events ("):
            return self._create_events(query, arguments)
        if query.strip().startswith("insert into collectionfields ("):
            return self._attach_fields_to_positions(query, arguments)
        if query.strip().startswith("insert into events_to_collectionfields ("):
            return self._attach_fields_to_events(query, arguments)

    def _create_position(self, query, arguments):
        """"""

    def _update_models(self, query, arguments):
        """"""

    def _update_id_sequences(self, query, arguments):
        """"""

    def _create_events(self, query, arguments):
        """"""

    def _attach_fields_to_positions(self, query, arguments):
        """"""

    def _attach_fields_to_events(self, query, arguments):
        """"""


@pytest.fixture(autouse=True)
def setup_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, FakeConnectionHandler)
    injector.register_as_singleton(ReadDatabase, MagicMock)
    injector.register_as_singleton(EventTranslator, EventTranslatorService)
    injector.register(Database, SqlDatabaseBackendService)
    injector.register(EnvironmentService, EnvironmentService)
    core_setup_di()


@pytest.fixture()
def write_handler():
    yield WriteHandler()


@pytest.fixture()
def connection_handler():
    yield injector.get(ConnectionHandler)


@pytest.fixture()
def read_db():
    yield injector.get(ReadDatabase)


@pytest.fixture()
def valid_metadata():
    yield copy.deepcopy(
        {"user_id": 1, "information": {}, "locked_fields": {}, "events": []}
    )


def test_insert_create_event(
    write_handler, connection_handler, valid_metadata, read_db
):
    fqid = "a/1"
    valid_metadata["events"].append(
        {"type": "create", "fqid": fqid, "fields": {"f": 1}}
    )
    position = MagicMock()
    connection_handler._create_position = cp = MagicMock(return_value=position)
    connection_handler._update_models = um = MagicMock()
    connection_handler._update_id_sequences = uis = MagicMock()
    event_id = MagicMock()
    connection_handler._create_events = ce = MagicMock(return_value=[event_id])
    collectionfield_id = MagicMock()
    connection_handler._attach_fields_to_positions = afp = MagicMock(
        return_value=[collectionfield_id]
    )
    connection_handler._attach_fields_to_events = afe = MagicMock()
    read_db.get_many = gm = MagicMock(return_value={})

    write_handler.write(valid_metadata)

    cp.assert_called_once()
    gm.assert_called_once()
    um.assert_called_once()
    assert fqid in um.call_args.args[1][0]

    uis.assert_called_once()
    ce.assert_called_once()
    assert fqid in ce.call_args.args[1][0]
    assert position in ce.call_args.args[1][0]

    afp.assert_called_once()
    afe.assert_called_once()


def test_insert_create_event_already_exists(
    write_handler, connection_handler, valid_metadata, read_db
):
    fqid = "a/1"
    valid_metadata["events"].append({"type": "create", "fqid": fqid, "fields": {}})
    connection_handler._create_position = cp = MagicMock()
    connection_handler._create_events = ce = MagicMock()
    read_db.get_many = MagicMock(return_value={fqid: {}})

    with pytest.raises(ModelExists) as e:
        write_handler.write(valid_metadata)

    cp.assert_called_once()
    assert fqid == e.value.fqid
    assert ce.call_count == 0


def test_combined_update_delete_fields_events(
    write_handler, connection_handler, valid_metadata, read_db
):
    fqid = "a/1"
    valid_metadata["events"].append(
        {"type": "update", "fqid": "a/1", "fields": {"f": 1, "none": None}}
    )
    position = MagicMock()
    connection_handler._create_position = cp = MagicMock(return_value=position)
    connection_handler._create_events = ce = MagicMock()
    connection_handler._attach_fields_to_positions = af = MagicMock()
    read_db.get_many = MagicMock(
        return_value={fqid: {"none": "a", META_DELETED: False}}
    )

    write_handler.write(valid_metadata)

    cp.assert_called_once()
    ce.assert_called_once()
    af.assert_called_once()
    # check if position is in the arguments
    assert position in ce.call_args.args[1][0]


def test_combined_update_delete_fields_events_model_not_existent(
    write_handler, connection_handler, valid_metadata, read_db
):
    valid_metadata["events"].append(
        {"type": "update", "fqid": "a/1", "fields": {"f": 1, "none": None}}
    )
    connection_handler._create_position = cp = MagicMock()
    connection_handler._create_events = ce = MagicMock()
    read_db.get_many = MagicMock(return_value={})

    with pytest.raises(ModelDoesNotExist) as e:
        write_handler.write(valid_metadata)

    cp.assert_called_once()
    assert "a/1" == e.value.fqid
    ce.assert_not_called()
