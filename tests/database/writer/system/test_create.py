from typing import Any
from unittest.mock import MagicMock

import pytest
from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import ModelExists
from openslides_backend.shared.interfaces.event import EventType
from openslides_backend.shared.patterns import (
    collection_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from tests.database.writer.system.util import (
    assert_db_entries,
    assert_model,
    create_model,
    create_write_requests,
    get_data,
)


def base_test_create_model(
    db_connection: Connection, data: list[dict[str, Any]]
) -> None:
    create_model(data)
    for request_data in data:
        for event in request_data["events"]:
            if fqid := event.get("fqid"):
                event["fields"]["id"] = id_from_fqid(fqid)
            else:
                fqid = fqid_from_collection_and_id(event["collection"], 1)
            assert_model(fqid, event["fields"])


def test_create_simple(db_connection: Connection) -> None:
    base_test_create_model(db_connection, get_data())


def test_create_collection(db_connection: Connection) -> None:
    data = get_data()
    event = data[0]["events"][0]
    event["collection"] = collection_from_fqid(event.pop("fqid"))
    base_test_create_model(db_connection, data)


def test_create_twice(db_connection: Connection) -> None:
    data = get_data()
    data.append(data[0])

    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(ModelExists) as e_info:
            extended_database.write(create_write_requests(data))
    assert "user/1" == e_info.value.fqid
    assert_db_entries(db_connection.cursor(), 1)


# TODO really create first, even though it is twice the same in one function call?


def test_update_twice(db_connection: Connection) -> None:
    data = get_data()
    base_test_create_model(db_connection, data)
    data[0]["events"] = [
        {
            "type": EventType.Update,
            "fqid": "user/1",
            "fields": {"username": "None", "first_name": None},
        },
        {
            "type": EventType.Update,
            "fqid": "user/1",
            "fields": {"username": "Some", "last_name": "1"},
        },
    ]

    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(
        "user/1", {"id": 1, "username": "Some", "first_name": None, "last_name": "1"}
    )


# def test_increased_id_sequence(db_connection: Connection, db_cur: Cursor, extended_database: ExtendedDatabase
# ) -> None:
#     create_model(db_connection, db_cur, extended_database)
#     db_cur.execute("SELECT id FROM id_sequences WHERE collection = %s", ["a"])
#     assert db_cur.fetchone()["id"] == 2


# def test_create_double_increased_id_sequence(db_connection: Connection, db_cur: Cursor, extended_database: ExtendedDatabase
# ) -> None:
#     create_model(db_connection, db_cur, extended_database)
#     data["events"][0]["fqid"] = "a/3"
#     response = json_client.post(WRITE_URL, data)
#     assert_response_code(response, 201)
#     db_cur.execute("SELECT id FROM id_sequences WHERE collection = %s", ["a"])
#     assert db_cur.fetchone()["id"] == 4


# def test_create_empty_field(db_connection: Connection, db_cur: Cursor, extended_database: ExtendedDatabase
# ) -> None:
#     data["events"][0]["fields"]["empty"] = None
#     response = json_client.post(WRITE_URL, data)
#     assert_response_code(response, 201)
#     assert_model("a/1", {"f": 1}, 1)
