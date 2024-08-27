import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend import (
    ALL_TABLES,
    ConnectionHandler,
)
from openslides_backend.datastore.shared.postgresql_backend.sql_event_types import (
    EVENT_TYPE,
)
from openslides_backend.datastore.shared.services import ReadDatabase
from openslides_backend.datastore.shared.util import ModelDoesNotExist
from openslides_backend.shared.patterns import META_DELETED, META_POSITION


def assert_model(fqid, model, position):
    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        # read from read db
        read_db = injector.get(ReadDatabase)
        read_db_model = read_db.get(fqid)

        model[META_DELETED] = False
        model[META_POSITION] = position
        assert read_db_model == model

        # build model and assert that the last event is not a deleted.
        built_model = read_db.build_model_ignore_deleted(fqid)
        assert built_model == model
        event_type = connection_handler.query_single_value(
            "SELECT type FROM events WHERE fqid=%s ORDER BY position DESC, weight DESC LIMIT 1",
            [fqid],
        )
        assert (
            isinstance(event_type, str)
            and len(event_type) > 0
            and event_type != EVENT_TYPE.DELETE
        )


def assert_no_model(fqid):
    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        # read from read db
        read_db = injector.get(ReadDatabase)

        with pytest.raises(ModelDoesNotExist):
            read_db.get(fqid)

        # assert last event is a deleted one
        event_type = connection_handler.query_single_value(
            "SELECT type FROM events WHERE fqid=%s ORDER BY position DESC, weight DESC LIMIT 1",
            [fqid],
        )
        assert event_type in (EVENT_TYPE.DELETE, None)


def assert_no_db_entry(db_cur):
    for table in ALL_TABLES:
        db_cur.execute(f"SELECT COUNT(*) FROM {table}")
        assert db_cur.fetchone()["count"] == 0
