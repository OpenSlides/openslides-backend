import copy

import pytest

from openslides_backend.datastore.shared.flask_frontend import ERROR_CODES
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


def test_update(json_client, data):
    create_model(json_client, data)

    field_data = [True, None, {"test": "value"}]
    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "fields": {"f": None, "another_field": field_data},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"another_field": field_data}, 2)


def test_single_field_delete(json_client, data):
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "fields": {"another_field": None},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1}, 2)


def test_update_non_existing_1(json_client, data, db_cur):
    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": "value"}}
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)
    assert_no_db_entry(db_cur)


def test_update_non_existing_2(json_client, data, db_cur):
    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": None}}
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)
    assert_no_db_entry(db_cur)


def test_update_meta_field(json_client, data, db_cur):
    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "fields": {"meta_something": "test"},
    }
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
    assert_no_db_entry(db_cur)


def test_list_update_add_empty(json_client, data):
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"field": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1, "field": [1]}, 2)


def test_list_update_add_empty_2(json_client, data):
    data["events"][0]["fields"]["field"] = []
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"field": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1, "field": [1]}, 2)


def test_list_update_add_string(json_client, data):
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"field": ["str"]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1, "field": ["str"]}, 2)


def test_list_update_add_existing(json_client, data):
    data["events"][0]["fields"]["f"] = [42]
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"f": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": [42, 1]}, 2)


def test_list_update_add_no_array(json_client, data):
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"f": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
    assert_model("a/1", {"f": 1}, 1)


def test_list_update_add_invalid_entry(json_client, data):
    data["events"][0]["fields"]["f"] = [[1]]
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"f": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
    assert_model("a/1", {"f": [[1]]}, 1)


def test_list_update_add_duplicate(json_client, data):
    data["events"][0]["fields"]["f"] = [1]
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"f": [1, 2]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": [1, 2]}, 2)


def test_list_update_remove_empty_1(json_client, data):
    """Should do nothing, since the field is not there."""
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"field": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1}, 2)


def test_list_update_remove_empty_2(json_client, data):
    data["events"][0]["fields"]["field"] = []
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"field": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1, "field": []}, 2)


def test_list_update_remove_existing(json_client, data):
    data["events"][0]["fields"]["f"] = [42]
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"f": [42]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": []}, 2)


def test_list_update_remove_no_array(json_client, data):
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"f": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
    assert_model("a/1", {"f": 1}, 1)


def test_list_update_remove_invalid_entry(json_client, data):
    data["events"][0]["fields"]["f"] = [[1]]
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"f": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
    assert_model("a/1", {"f": [[1]]}, 1)


def test_list_update_remove_not_existent(json_client, data):
    data["events"][0]["fields"]["f"] = [1]
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"f": [42]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": [1]}, 2)


def test_list_update_remove_partially_not_existent(json_client, data):
    data["events"][0]["fields"]["f"] = [1]
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"f": [1, 42]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": []}, 2)


def test_list_update_add_remove(json_client, data):
    data["events"][0]["fields"]["f"] = [1]
    data["events"][0]["fields"]["f2"] = ["test"]
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"f": [2]}, "remove": {"f2": ["test"]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": [1, 2], "f2": []}, 2)


def test_list_update_add_remove_same_field(json_client, data):
    data["events"][0]["fields"]["f"] = [1]
    create_model(json_client, data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"f": [2]}, "remove": {"f": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": [2]}, 2)
