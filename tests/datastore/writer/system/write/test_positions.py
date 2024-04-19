import copy

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.services import ReadDatabase
from openslides_backend.datastore.shared.util import DeletedModelsBehaviour
from openslides_backend.datastore.writer.flask_frontend.routes import WRITE_URL
from tests.datastore.util import assert_response_code

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


def test_position_delete_restore(json_client, data):
    create_model(json_client, data)

    data["events"][0] = {"type": "delete", "fqid": "a/1"}
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)

    data["events"][0] = {"type": "restore", "fqid": "a/1"}
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)

    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        read_db = injector.get(ReadDatabase)
        read_db_model = read_db.get("a/1")

        assert read_db_model == {"f": 1, "meta_deleted": False, "meta_position": 3}


def test_position_delete(json_client, data):
    create_model(json_client, data)

    data["events"][0] = {"type": "delete", "fqid": "a/1"}
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)

    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        read_db = injector.get(ReadDatabase)
        read_db_model = read_db.get(
            "a/1", get_deleted_models=DeletedModelsBehaviour.ONLY_DELETED
        )

        assert read_db_model == {"f": 1, "meta_deleted": True, "meta_position": 2}


def test_position_update(json_client, data):
    create_model(json_client, data)

    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": 2}}
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)

    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        read_db = injector.get(ReadDatabase)
        read_db_model = read_db.get("a/1")

        assert read_db_model == {"f": 2, "meta_deleted": False, "meta_position": 2}


def test_position_delete_field(json_client, data):
    create_model(json_client, data)

    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": None}}
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)

    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        read_db = injector.get(ReadDatabase)
        read_db_model = read_db.get("a/1")

        assert read_db_model == {"meta_deleted": False, "meta_position": 2}


def test_position_list_update(json_client, data):
    data["events"][0]["fields"]["f"] = []
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"f": [42]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)

    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        read_db = injector.get(ReadDatabase)
        read_db_model = read_db.get("a/1")

        assert read_db_model == {"f": [42], "meta_deleted": False, "meta_position": 2}
