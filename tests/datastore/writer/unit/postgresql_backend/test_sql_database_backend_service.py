from unittest.mock import MagicMock, patch

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.services import ReadDatabase
from openslides_backend.datastore.shared.util import BadCodingError, InvalidFormat
from openslides_backend.datastore.writer.core.database import Database
from openslides_backend.datastore.writer.postgresql_backend import (
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbListUpdateEvent,
    DbRestoreEvent,
    DbUpdateEvent,
    EventTranslator,
    SqlDatabaseBackendService,
)
from openslides_backend.datastore.writer.postgresql_backend.sql_database_backend_service import (
    COLLECTION_MAX_LEN,
    COLLECTIONFIELD_MAX_LEN,
    FQID_MAX_LEN,
)
from openslides_backend.shared.patterns import META_DELETED, META_POSITION
from tests.datastore import reset_di  # noqa


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, MagicMock)
    injector.register_as_singleton(ReadDatabase, MagicMock)
    injector.register_as_singleton(EventTranslator, MagicMock)
    injector.register(Database, SqlDatabaseBackendService)
    yield


@pytest.fixture()
def sql_backend(provide_di):
    yield injector.get(Database)


@pytest.fixture()
def connection(provide_di):
    yield injector.get(ConnectionHandler)


@pytest.fixture()
def read_db(provide_di):
    yield injector.get(ReadDatabase)


@pytest.fixture()
def event_translator(provide_di):
    yield injector.get(EventTranslator)


def test_sql_backend_creation(sql_backend):
    assert bool(sql_backend)


def test_get_context(sql_backend, connection):
    connection.get_connection_context = MagicMock(return_value="my_return_value")

    assert sql_backend.get_context() == "my_return_value"


def test_json(sql_backend, connection):
    connection.to_json = tj = MagicMock(return_value="my_return_value")

    assert sql_backend.json("my_data") == "my_return_value"
    tj.assert_called_with("my_data")


class TestInsertEvents:
    def test_insert_no_events(self, sql_backend):
        sql_backend.create_position = cp = MagicMock()
        with pytest.raises(BadCodingError):
            sql_backend.insert_events([], 1, {}, 1)
        cp.assert_not_called()

    def test_set_position(self, sql_backend):
        sql_backend.create_position = MagicMock(return_value=239)
        event = MagicMock()
        event.fqid = "a/1"

        position, _ = sql_backend.insert_events([event], 1, {}, 1)

        assert position == 239

    def test_call_get_modified_fields(self, sql_backend, event_translator):
        sql_backend.create_position = MagicMock()
        sql_backend.apply_event_to_models = MagicMock()
        event_translator.translate = MagicMock(side_effect=lambda x, _: [x])
        event1 = MagicMock()
        event1.fqid = "a/1"
        value1 = MagicMock()
        event1.get_modified_fields = gmf1 = MagicMock(return_value={"f1": value1})
        event2 = MagicMock()
        event2.fqid = "a/2"
        value2 = MagicMock()
        event2.get_modified_fields = gmf2 = MagicMock(return_value={"f2": value2})

        _, modified_models = sql_backend.insert_events([event1, event2], 1, {}, 1)

        assert modified_models[event1.fqid] == {"f1": value1}
        assert modified_models[event2.fqid] == {"f2": value2}
        gmf1.assert_called()
        gmf2.assert_called()


def test_create_position(sql_backend, connection):
    sql_backend.json = json = MagicMock(side_effect=lambda data: data)
    connection.query_single_value = qsv = MagicMock(return_value=2844)

    position = sql_backend.create_position(1, {"some": "data", "is": ["given"]}, 42)

    assert position == 2844
    qsv.assert_called_once()
    json.assert_called_once()


class TestGetModelsFromEvents:
    def test_get_models_from_events(self, sql_backend, read_db):
        result = MagicMock()
        read_db.get_many = MagicMock(return_value=result)

        event = MagicMock()
        event.fqid = "a/1"
        models = sql_backend.get_models_from_events([event])
        assert models == result
        assert read_db.get_many.call_args.args[0] == {"a/1"}

    def test_fqid_multiple_times(self, sql_backend, read_db):
        result = MagicMock()
        read_db.get_many = MagicMock(return_value=result)

        event = MagicMock()
        event.fqid = "a/1"
        models = sql_backend.get_models_from_events([event] * 3)
        assert models == result
        assert read_db.get_many.call_args.args[0] == {"a/1"}

    def test_fqid_too_long(self, sql_backend, event_translator):
        event = MagicMock()
        event.fqid = "a/" + "1" * FQID_MAX_LEN

        with pytest.raises(InvalidFormat) as e:
            sql_backend.get_models_from_events([event])

        assert event.fqid in e.value.msg


class TestApplyEventToModels:
    def test_create_event(self, sql_backend):
        data = {"some": "data"}
        event = DbCreateEvent("a/1", data)
        models = {}
        position = MagicMock()
        sql_backend.apply_event_to_models(event, models, position)
        assert models["a/1"] == {
            "some": "data",
            META_POSITION: position,
            META_DELETED: False,
        }
        assert data == {"some": "data"}  # assert that event data was not changed

    def test_update_event(self, sql_backend):
        data = {"some": "data"}
        event = DbUpdateEvent("a/1", data)
        models = {"a/1": {"other": "field"}}
        position = MagicMock()
        sql_backend.apply_event_to_models(event, models, position)
        assert models["a/1"] == {
            "other": "field",
            "some": "data",
            META_POSITION: position,
        }
        assert data == {"some": "data"}

    def test_list_update_event(self, sql_backend):
        add = {"f": [1]}
        remove = {"g": [2]}
        models = {"a/1": {"other": "field", "g": [2]}}
        event = DbListUpdateEvent("a/1", add, remove, models["a/1"])
        position = MagicMock()
        sql_backend.apply_event_to_models(event, models, position)
        assert models["a/1"] == {
            "other": "field",
            "f": [1],
            "g": [],
            META_POSITION: position,
        }

    def test_delete_fields_event(self, sql_backend):
        event = DbDeleteFieldsEvent("a/1", ["field"])
        models = {"a/1": {"field": "data"}}
        position = MagicMock()
        sql_backend.apply_event_to_models(event, models, position)
        assert models["a/1"] == {META_POSITION: position}

    def test_delete_event(self, sql_backend):
        event = DbDeleteEvent("a/1", ["field"])
        models = {"a/1": {"field": "data"}}
        position = MagicMock()
        sql_backend.apply_event_to_models(event, models, position)
        assert models["a/1"] == {
            "field": "data",
            META_POSITION: position,
            META_DELETED: True,
        }

    def test_restore_event(self, sql_backend):
        event = DbRestoreEvent("a/1", ["field"])
        models = {"a/1": {"field": "data"}}
        position = MagicMock()
        sql_backend.apply_event_to_models(event, models, position)
        assert models["a/1"] == {
            "field": "data",
            META_POSITION: position,
            META_DELETED: False,
        }

    def test_invalid_event(self, sql_backend):
        with pytest.raises(BadCodingError):
            sql_backend.apply_event_to_models(MagicMock(), {}, MagicMock())


def test_write_model_updates(sql_backend, connection):
    connection.execute = execute = MagicMock()
    sql_backend.json = MagicMock(side_effect=lambda data: data)

    sql_backend.write_model_updates(
        {
            "a/1": {"f": 1, META_DELETED: False},
            "a/2": {"f": 1, META_DELETED: True},
        }
    )

    execute.assert_called_once()
    assert execute.call_args.args[0].startswith("insert into models (")
    assert execute.call_args.args[1] == [
        ("a/1", {"f": 1, META_DELETED: False}, False),
        ("a/2", {"f": 1, META_DELETED: True}, True),
    ]


def test_update_id_sequences(sql_backend, connection):
    connection.execute = execute = MagicMock()

    sql_backend.update_id_sequences({"a": 1, "b": 2})

    execute.assert_called_once()
    assert execute.call_args.args[0].startswith("insert into id_sequences (")
    assert execute.call_args.args[1] == [("a", 1), ("b", 2)]


def test_write_events(sql_backend, connection):
    result = MagicMock()
    connection.query_list_of_single_values = qlosv = MagicMock(return_value=result)
    events = MagicMock()

    assert sql_backend.write_events(events) == result

    qlosv.assert_called_once()
    assert qlosv.call_args.args[0].startswith("insert into events (")
    assert qlosv.call_args.args[1] == events


class TestAttachModifiedFieldsToEvents:
    def test_get_modified_collectionfields_from_event(self, sql_backend):
        event = MagicMock()
        field = MagicMock()
        event.get_modified_fields = MagicMock(return_value=[field])
        event.fqid = MagicMock()
        with patch(
            "openslides_backend.datastore.writer.postgresql_backend.sql_database_backend_service.collectionfield_from_fqid_and_field"
        ) as cffaf:
            result = MagicMock()
            cffaf.side_effect = lambda x, y: result

            assert sql_backend.get_modified_collectionfields_from_event(event) == [
                result
            ]

            cffaf.assert_called_with(event.fqid, field)

    def test_insert_modified_collectionfields_into_db(self, sql_backend, connection):
        collectionfield_ids = MagicMock()
        connection.query_list_of_single_values = qlosv = MagicMock(
            return_value=collectionfield_ids
        )
        collectionfield = MagicMock()
        position = MagicMock()

        sql_backend.insert_modified_collectionfields_into_db(
            [collectionfield], position
        )
        assert qlosv.call_args.args[1] == [(collectionfield, position)]

    def test_insert_modified_collectionfields_into_db_too_long(
        self, sql_backend, connection
    ):
        connection.query_list_of_single_values = qlosv = MagicMock()
        collectionfield = "c/" + "f" * COLLECTIONFIELD_MAX_LEN

        with pytest.raises(InvalidFormat) as e:
            sql_backend.insert_modified_collectionfields_into_db(
                [collectionfield], MagicMock()
            )

        assert collectionfield in e.value.msg
        qlosv.assert_not_called()

    def test_connect_events_and_collection_fields(self, sql_backend, connection):
        connection.execute = ex = MagicMock()
        event_ids = [MagicMock(), MagicMock()]
        collectionfield_ids = [MagicMock(), MagicMock()]
        event_indices_order = [[0], [0, 1]]

        sql_backend.connect_events_and_collection_fields(
            event_ids, collectionfield_ids, event_indices_order
        )

        ex.assert_called_once()
        assert ex.call_args.args[1] == [
            (event_ids[0], collectionfield_ids[0]),
            (event_ids[0], collectionfield_ids[1]),
            (event_ids[1], collectionfield_ids[1]),
        ]


class TestReserveNextIds:
    def test_wrong_amount(self, sql_backend):
        with pytest.raises(InvalidFormat):
            sql_backend.reserve_next_ids("my_collection", 0)

    def test_empty_collection(self, sql_backend):
        with pytest.raises(InvalidFormat):
            sql_backend.reserve_next_ids("", 1)

    def test_collection_too_long(self, sql_backend):
        with pytest.raises(InvalidFormat):
            sql_backend.reserve_next_ids("x" * (COLLECTION_MAX_LEN + 1), 1)

    def test_initial_collection_query(self, sql_backend, connection):
        connection.query_single_value = qsv = MagicMock(return_value=4)

        result = sql_backend.reserve_next_ids("my_collection", 3)

        assert result == [1, 2, 3]
        args = qsv.call_args.args[1]
        assert args == ["my_collection", 4]

    def test_collection_query(self, sql_backend, connection):
        connection.query_single_value = qsv = MagicMock(return_value=7)

        result = sql_backend.reserve_next_ids("my_collection", 3)

        assert result == [4, 5, 6]
        args = qsv.call_args.args[1]
        assert args == ["my_collection", 4]


def test_delete_history_information(sql_backend, connection):
    connection.execute = ex = MagicMock()
    sql_backend.delete_history_information()
    assert ex.call_count == 1
    assert ex.call_args[0][0] == "UPDATE positions SET information = NULL;"
