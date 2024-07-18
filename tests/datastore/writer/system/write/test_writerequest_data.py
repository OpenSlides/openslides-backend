from datetime import datetime

from openslides_backend.datastore.writer.flask_frontend.routes import WRITE_URL
from tests.datastore.util import assert_response_code


def test_user_id_and_information(json_client, db_cur):
    response = json_client.post(
        WRITE_URL,
        {
            "user_id": 42,
            "information": {"k": "v"},
            "locked_fields": {},
            "events": [{"type": "create", "fqid": "a/1", "fields": {}}],
        },
    )
    assert_response_code(response, 201)

    db_cur.execute("select user_id, information from positions where position=%s", [1])
    row = db_cur.fetchone()
    assert row["user_id"] == 42
    assert row["information"] == {"k": "v"}


def test_timestamp(json_client, db_cur):
    start = datetime.now().timestamp()
    response = json_client.post(
        WRITE_URL,
        {
            "user_id": 1,
            "information": {"k": "v"},
            "locked_fields": {},
            "events": [{"type": "create", "fqid": "a/1", "fields": {}}],
        },
    )
    end = datetime.now().timestamp()
    assert_response_code(response, 201)

    db_cur.execute("select timestamp from positions where position=%s", [1])
    timestamp = db_cur.fetchone()["timestamp"].timestamp()
    assert timestamp > start
    assert timestamp < end


def test_empty_information(json_client, db_cur):
    for i, value in enumerate(
        (
            0,
            [],
            {},
            False,
            "",
            None,
        )
    ):
        response = json_client.post(
            WRITE_URL,
            {
                "user_id": 1,
                "information": value,
                "locked_fields": {},
                "events": [{"type": "create", "fqid": f"a/{i+1}", "fields": {}}],
            },
        )
        assert_response_code(response, 201)

    db_cur.execute("select information from positions")
    for result in db_cur.fetchall():
        assert result["information"] is None
