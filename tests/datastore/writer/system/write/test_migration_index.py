import copy

import pytest

from openslides_backend.datastore.shared.flask_frontend import ERROR_CODES
from openslides_backend.datastore.writer.flask_frontend.routes import WRITE_URL
from tests.datastore.util import assert_error_response, assert_response_code
from tests.datastore.writer.system.util import assert_model

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


def test_initial_migration_index(json_client, data, db_cur):
    create_model(json_client, data)

    db_cur.execute("SELECT migration_index FROM positions WHERE position=%s", [1])
    migration_index = db_cur.fetchone()["migration_index"]
    assert migration_index == -1


def test_use_current_migration_index(json_client, data, db_connection, db_cur):
    create_model(json_client, data)

    # change the migration index and reset the read DB
    db_cur.execute("UPDATE positions SET migration_index=3 WHERE position=1", [])
    db_connection.commit()

    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": 2}}
    response = json_client.post(WRITE_URL, [data])
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 2}, 2)

    db_cur.execute("SELECT migration_index FROM positions WHERE position=%s", [2])
    migration_index = db_cur.fetchone()["migration_index"]
    assert migration_index == 3


def test_varying_migration_indices(json_client, data, db_connection, db_cur):
    # create two positions
    create_model(json_client, data)

    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": 2}}
    response = json_client.post(WRITE_URL, [data])
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 2}, 2)

    # modify the migration index of the second position and reset the read db
    db_cur.execute("UPDATE positions SET migration_index=3 WHERE position=2", [])
    db_connection.commit()

    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": 3}}
    response = json_client.post(WRITE_URL, [data])
    assert_error_response(response, ERROR_CODES.INVALID_DATASTORE_STATE)
    assert_model("a/1", {"f": 2}, 2)


def test_send_migration_index(json_client, data, db_cur):
    data["migration_index"] = 3
    create_model(json_client, data)

    db_cur.execute("SELECT migration_index FROM positions WHERE position=%s", [1])
    migration_index = db_cur.fetchone()["migration_index"]
    assert migration_index == 3


def test_send_migration_index_not_empty(json_client, data, db_cur):
    create_model(json_client, data)

    data["events"][0]["fqid"] = "a/2"
    data["migration_index"] = 3
    response = json_client.post(WRITE_URL, [data])
    assert_error_response(response, ERROR_CODES.DATASTORE_NOT_EMPTY)
    assert (
        "Passed a migration index of 3, but the datastore is not empty."
        == response.json["error"]["msg"]
    )

    db_cur.execute("SELECT migration_index FROM positions WHERE position=%s", [1])
    migration_index = db_cur.fetchone()["migration_index"]
    assert migration_index == -1
