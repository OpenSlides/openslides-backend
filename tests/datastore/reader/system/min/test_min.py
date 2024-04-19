from openslides_backend.datastore.reader.flask_frontend.routes import Route
from openslides_backend.datastore.shared.flask_frontend import ERROR_CODES
from tests.datastore import assert_error_response
from tests.datastore.reader.system.util import setup_data
from tests.datastore.util import assert_success_response

data = {
    "a/1": {"field_1": "d", "meta_position": 2, "field_2": 1},
    "a/2": {"field_1": "c", "meta_position": 3, "field_2": 1},
    "a/3": {"field_1": "b", "meta_position": 4},
    "b/1": {"field_1": "a", "meta_position": 5},
}


def test_simple(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.MIN.URL,
        {
            "collection": "a",
            "filter": {"field": "field_1", "operator": "!=", "value": "invalid"},
            "field": "meta_position",
        },
    )
    assert_success_response(response)
    assert response.json == {
        "min": 2,
        "position": 5,
    }


def test_with_type(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.MIN.URL,
        {
            "collection": "a",
            "filter": {"field": "meta_position", "operator": ">", "value": 2},
            "field": "meta_position",
            "type": "int",
        },
    )
    assert_success_response(response)
    assert response.json == {
        "min": 3,
        "position": 5,
    }


def test_no_results(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.MIN.URL,
        {
            "collection": "a",
            "filter": {"field": "field_1", "operator": "=", "value": "invalid"},
            "field": "meta_position",
        },
    )
    assert_success_response(response)
    assert response.json == {
        "min": None,
        "position": 5,
    }


def test_invalid_collection(json_client):
    response = json_client.post(
        Route.MIN.URL,
        {
            "collection": "not valid",
            "filter": {"field": "field", "operator": "=", "value": "data"},
            "field": "field",
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_field(json_client):
    response = json_client.post(
        Route.MIN.URL,
        {
            "collection": "collection",
            "filter": {"field": "field", "operator": "=", "value": "data"},
            "field": "not valid",
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_filter_field(json_client):
    response = json_client.post(
        Route.MIN.URL,
        {
            "collection": "a",
            "filter": {"field": "not valid", "operator": "=", "value": "data"},
            "field": "field",
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_operator(json_client):
    response = json_client.post(
        Route.MIN.URL,
        {
            "collection": "a",
            "filter": {"field": "field", "operator": "invalid", "value": "data"},
            "field": "field",
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)
