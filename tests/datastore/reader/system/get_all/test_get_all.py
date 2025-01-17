import json

from openslides_backend.datastore.reader.flask_frontend.routes import Route
from openslides_backend.datastore.shared.flask_frontend import ERROR_CODES
from tests.datastore import assert_error_response
from tests.datastore.util import assert_success_response

data = {
    "a/1": {
        "field_4": "data",
        "field_5": 42,
        "field_6": [1, 2, 3],
        "meta_position": 2,
    },
    "a/2": {
        "field_4": "data",
        "field_5": 42,
        "field_6": [1, 2, 3],
        "meta_position": 3,
    },
}
other_models = {
    "b/1": {"field_1": "data", "field_2": 42, "field_3": [1, 2, 3], "meta_position": 1}
}


def setup_data(connection, cursor, deleted=999):
    for i, (fqid, model) in enumerate(list(data.items()) + list(other_models.items())):
        cursor.execute(
            "insert into models (fqid, data, deleted) values (%s, %s, %s)",
            [fqid, json.dumps(model), (i + 1) % deleted == 0],
        )
    connection.commit()


def test_simple(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(Route.GET_ALL.URL, {"collection": "a"})
    assert_success_response(response)
    assert response.json == {"1": data["a/1"], "2": data["a/2"]}


def test_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, 2)
    response = json_client.post(Route.GET_ALL.URL, {"collection": "a"})
    assert_success_response(response)
    assert response.json == {"1": data["a/1"]}


def test_mapped_fields(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.GET_ALL.URL,
        {"collection": "a", "mapped_fields": ["field_4", "meta_position"]},
    )
    assert_success_response(response)
    assert response.json == {
        "1": {"field_4": "data", "meta_position": 2},
        "2": {"field_4": "data", "meta_position": 3},
    }


def test_invalid_collection(json_client):
    response = json_client.post(Route.GET_ALL.URL, {"collection": "not valid"})
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_mapped_fields(json_client):
    response = json_client.post(
        Route.GET_ALL.URL, {"collection": "a", "mapped_fields": ["not valid"]}
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
