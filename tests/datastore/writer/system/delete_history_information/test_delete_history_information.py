from openslides_backend.datastore.writer.flask_frontend.routes import (
    DELETE_HISTORY_INFORMATION_URL,
)
from tests.datastore.util import assert_response_code


def test_delete_history_information(db_connection, db_cur, json_client):
    db_cur.execute(
        "insert into positions (user_id, migration_index, information) values (1, 1, to_json('test'::text))"
    )
    db_connection.commit()

    response = json_client.post(DELETE_HISTORY_INFORMATION_URL, {})
    assert_response_code(response, 204)

    with db_connection.cursor() as cursor:
        cursor.execute("select information from positions")
        assert cursor.fetchone()["information"] is None
