import copy

import pytest

from openslides_backend.datastore.shared.flask_frontend import ERROR_CODES
from openslides_backend.datastore.writer.flask_frontend.routes import (
    WRITE_URL,
    WRITE_WITHOUT_EVENTS_URL,
)
from openslides_backend.shared.patterns import META_FIELD_PREFIX
from tests.datastore.util import assert_error_response
from tests.datastore.writer.system.util import assert_no_db_entry


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


@pytest.fixture(autouse=True)
def check_no_db_entry(db_cur):
    yield
    assert_no_db_entry(db_cur)


def test_wrong_format(json_client):
    response = json_client.post(WRITE_URL, ["not_valid", None])
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_no_json_write(client):
    response = client.post(WRITE_URL, data={"some": "data"})
    assert response.is_json
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_no_json_write_without_events(client):
    response = client.post(WRITE_WITHOUT_EVENTS_URL, data={"some": "data"})
    assert response.is_json
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_missing_user_id(json_client, data):
    del data["user_id"]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_missing_information(json_client, data):
    del data["information"]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_missing_locked_fields(json_client, data):
    del data["locked_fields"]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_missing_events(json_client, data):
    del data["events"]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_empty_events(json_client, data):
    data["events"] = []
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_unknown_event(json_client, data):
    data["events"][0]["type"] = "unknown"
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_missing_fqid(json_client, data):
    del data["events"][0]["fqid"]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_create_invalid_fqid(json_client, data):
    data["events"][0]["fqid"] = "not valid"
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_create_missing_fields(json_client, data):
    del data["events"][0]["fields"]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_create_invalid_field(json_client, data):
    data["events"][0]["fields"] = {META_FIELD_PREFIX: "value"}
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_update_empty_fields(json_client, data):
    data["events"][0]["fields"] = {}
    data["events"][0]["type"] = "update"
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_update_missing_fields(json_client, data):
    del data["events"][0]["fields"]
    data["events"][0]["type"] = "update"
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_update_invalid_field(json_client, data):
    data["events"][0]["fields"] = {META_FIELD_PREFIX: "value"}
    data["events"][0]["type"] = "update"
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_update_list_update_duplicate_field(json_client, data):
    data["events"].append(
        {
            "type": "update",
            "fqid": "a/1",
            "fields": {"f": [2]},
            "list_fields": {"add": {"f": [3]}},
        }
    )
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_update_no_fields(json_client, data):
    data["events"].append(
        {
            "type": "update",
            "fqid": "a/1",
            "fields": {},
            "list_fields": {},
        }
    )
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_list_update_invalid_key(json_client, data):
    data["events"].append(
        {
            "type": "update",
            "fqid": "a/1",
            "fields": {"g": 1},
            "list_fields": {"invalid": {"field": [1]}},
        }
    )
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_locked_fields_invalid_key(json_client, data):
    for key in ("collection", "_collection/field", "c/c/f", "1/1/1"):
        data["locked_fields"] = {key: 1}

        response = json_client.post(WRITE_URL, data)
        assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_lock_negative_position(json_client, data):
    data["locked_fields"]["a/1"] = -1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_lock_zero_position(json_client, data):
    data["locked_fields"]["a/1"] = 0

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_lock_null_position(json_client, data):
    data["locked_fields"]["a/1"] = None

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_migration_index_string(json_client, data):
    data["migration_index"] = "should be int"

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_migration_index_zero(json_client, data):
    data["migration_index"] = 0

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_migration_index_negative(json_client, data):
    data["migration_index"] = -1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)
