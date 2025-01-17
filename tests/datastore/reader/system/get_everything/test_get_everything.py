import json

from openslides_backend.datastore.reader.flask_frontend.routes import Route
from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.services import EnvironmentService
from openslides_backend.datastore.shared.services.environment_service import (
    DATASTORE_DEV_MODE_ENVIRONMENT_VAR,
)
from openslides_backend.shared.patterns import id_from_fqid
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
        "meta_position": 2,
    },
    "b/1": {
        "field_4": "data",
        "field_5": 42,
        "field_6": [1, 2, 3],
        "meta_position": 3,
    },
}


def setup_data(connection, cursor):
    # a/2 is deleted
    for fqid, model in data.items():
        cursor.execute(
            "insert into models (fqid, data, deleted) values (%s, %s, %s)",
            [fqid, json.dumps(model), fqid == "a/2"],
        )
    connection.commit()


def get_data_with_id(fqid):
    model = data[fqid]
    model["id"] = id_from_fqid(fqid)
    return model


def test_simple(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(Route.GET_EVERYTHING.URL, {})
    assert_success_response(response)
    assert response.json == {
        "a": {"1": get_data_with_id("a/1")},
        "b": {"1": get_data_with_id("b/1")},
    }


def test_prod(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    injector.get(EnvironmentService).set(DATASTORE_DEV_MODE_ENVIRONMENT_VAR, "0")
    response = json_client.post(Route.GET_EVERYTHING.URL, {})
    assert_success_response(response)
    assert response.json == {
        "a": {"1": get_data_with_id("a/1")},
        "b": {"1": get_data_with_id("b/1")},
    }
