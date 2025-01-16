import json
from datetime import datetime

import pytest

from openslides_backend.datastore.reader.flask_frontend.routes import Route
from openslides_backend.services.database.event_types import EVENT_TYPE
from tests.datastore.util import assert_success_response


@pytest.fixture()
def setup(db_connection, db_cur):
    def _setup(fqid, user_id, information, timestamp):
        db_cur.execute(
            """INSERT INTO positions (user_id, information, timestamp, migration_index)
            VALUES (%s, %s, %s, 1) RETURNING position""",
            [user_id, json.dumps(information), timestamp],
        )
        position = db_cur.fetchone()["position"]
        db_cur.execute(
            "INSERT INTO events (position, fqid, type, data, weight) VALUES (%s, %s, %s, %s, 1)",
            [position, fqid, EVENT_TYPE.CREATE, json.dumps({})],
        )
        db_connection.commit()

    yield _setup


def test_simple(setup, json_client):
    now = datetime.now()
    setup("a/1", 42, ["test"], now)
    response = json_client.post(Route.HISTORY_INFORMATION.URL, {"fqids": ["a/1"]})
    assert_success_response(response)
    assert response.json == {
        "a/1": [
            {
                "position": 1,
                "user_id": 42,
                "information": ["test"],
                "timestamp": now.timestamp(),
            }
        ]
    }


def test_multiple_models(setup, json_client):
    now = datetime.now()
    setup("a/1", 42, ["test1"], now)
    setup("a/2", 42, ["test2"], now)
    setup("a/3", 42, ["test3"], now)
    response = json_client.post(
        Route.HISTORY_INFORMATION.URL, {"fqids": ["a/1", "a/2"]}
    )
    assert_success_response(response)
    assert response.json == {
        "a/1": [
            {
                "position": 1,
                "user_id": 42,
                "information": ["test1"],
                "timestamp": now.timestamp(),
            }
        ],
        "a/2": [
            {
                "position": 2,
                "user_id": 42,
                "information": ["test2"],
                "timestamp": now.timestamp(),
            }
        ],
    }


def test_multiple_models_2(setup, json_client):
    now = datetime.now()
    setup("a/1", 42, ["test1"], now)
    setup("a/2", 42, ["test2"], now)
    setup("a/3", 42, ["test3"], now)
    response = json_client.post(Route.HISTORY_INFORMATION.URL, {"fqids": ["a/2"]})
    assert_success_response(response)
    assert response.json == {
        "a/2": [
            {
                "position": 2,
                "user_id": 42,
                "information": ["test2"],
                "timestamp": now.timestamp(),
            }
        ]
    }


def test_empty(json_client):
    response = json_client.post(Route.HISTORY_INFORMATION.URL, {"fqids": ["a/1"]})
    assert_success_response(response)
    assert response.json == {}


def test_skip_empty_information(setup, json_client):
    now = datetime.now()
    setup("a/1", 2, None, now)
    setup("a/1", 3, ["test"], now)
    setup("a/1", 4, None, now)
    response = json_client.post(Route.HISTORY_INFORMATION.URL, {"fqids": ["a/1"]})
    assert_success_response(response)
    assert response.json == {
        "a/1": [
            {
                "position": 2,
                "user_id": 3,
                "information": ["test"],
                "timestamp": now.timestamp(),
            }
        ]
    }
