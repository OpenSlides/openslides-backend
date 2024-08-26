import copy

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.flask_frontend import ERROR_CODES
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.writer.flask_frontend.routes import WRITE_URL
from tests.datastore.util import assert_error_response, assert_response_code
from tests.datastore.writer.system.util import assert_model, assert_no_db_entry

from .test_write import create_model


@pytest.fixture()
def data():
    yield copy.deepcopy(
        {
            "user_id": 1,
            "information": {},
            "locked_fields": {},
            "events": [{"type": "create", "fqid": "a/1", "fields": {"f": 1}}],
        }
    )


@pytest.fixture()
def connection_handler():
    yield injector.get(ConnectionHandler)


def test_create_simple(json_client, data):
    create_model(json_client, data)


def test_increased_id_sequence(json_client, data, db_cur):
    create_model(json_client, data)
    db_cur.execute("SELECT id FROM id_sequences WHERE collection = %s", ["a"])
    assert db_cur.fetchone()["id"] == 2


def test_create_double_increased_id_sequence(json_client, data, db_cur):
    create_model(json_client, data)
    data["events"][0]["fqid"] = "a/3"
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    db_cur.execute("SELECT id FROM id_sequences WHERE collection = %s", ["a"])
    assert db_cur.fetchone()["id"] == 4


def test_create_empty_field(json_client, data):
    data["events"][0]["fields"]["empty"] = None
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1}, 1)


def test_create_meta_field(json_client, data, db_cur):
    data["events"][0]["fields"]["meta_something"] = "test"
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
    assert_no_db_entry(db_cur)


def test_create_twice(json_client, data, db_cur):
    data["events"].append(data["events"][0])
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_EXISTS)
    assert_no_db_entry(db_cur)


def test_create_no_meta_fields_in_db(json_client, data, connection_handler):
    create_model(json_client, data)
    with connection_handler.get_connection_context():
        event_data = connection_handler.query_single_value(
            "SELECT data FROM events WHERE id=1", []
        )
        assert event_data == {"f": 1}
