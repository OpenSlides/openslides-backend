from openslides_backend.datastore.shared.flask_frontend import ERROR_CODES
from openslides_backend.datastore.writer.flask_frontend.routes import RESERVE_IDS_URL
from openslides_backend.datastore.writer.postgresql_backend.sql_database_backend_service import (
    COLLECTION_MAX_LEN,
)
from tests.datastore.util import assert_error_response


def test_simple(json_client, db_cur):
    response = json_client.post(
        RESERVE_IDS_URL, {"amount": 1, "collection": "test_collection"}
    )
    assert response.status_code == 200

    assert response.json == {"ids": [1]}
    db_cur.execute("select * from id_sequences")
    result = db_cur.fetchall()
    assert result == [("test_collection", 2)]


def test_multiple(json_client, db_cur):
    response = json_client.post(
        RESERVE_IDS_URL, {"amount": 3, "collection": "test_collection"}
    )
    assert response.status_code == 200

    assert response.json == {"ids": [1, 2, 3]}
    db_cur.execute("select * from id_sequences")
    result = db_cur.fetchall()
    assert result == [("test_collection", 4)]


def test_successive(json_client, db_cur):
    response = json_client.post(
        RESERVE_IDS_URL, {"amount": 3, "collection": "test_collection"}
    )
    assert response.status_code == 200

    response = json_client.post(
        RESERVE_IDS_URL, {"amount": 4, "collection": "test_collection"}
    )
    assert response.status_code == 200

    assert response.json == {"ids": [4, 5, 6, 7]}
    db_cur.execute("select * from id_sequences")
    result = db_cur.fetchall()
    assert result == [("test_collection", 8)]


def assert_no_db_entry(db_cur):
    db_cur.execute("select count(*) from id_sequences")
    assert db_cur.fetchone()[0] == 0


def test_wrong_format(json_client, db_cur):
    response = json_client.post(RESERVE_IDS_URL, ["not_valid", None])
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)
    assert_no_db_entry(db_cur)


def test_negative_amount(json_client, db_cur):
    response = json_client.post(
        RESERVE_IDS_URL, {"amount": -1, "collection": "test_collection"}
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
    assert_no_db_entry(db_cur)


def test_too_long_collection(json_client, db_cur):
    response = json_client.post(
        RESERVE_IDS_URL, {"amount": 1, "collection": "x" * (COLLECTION_MAX_LEN + 1)}
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
    assert_no_db_entry(db_cur)


def test_no_json(client):
    response = client.post(
        RESERVE_IDS_URL, data={"amount": 1, "collection": "test_collection"}
    )
    assert response.is_json
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)
