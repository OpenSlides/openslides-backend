from typing import Any
from unittest.mock import MagicMock

import pytest
from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import ModelExists
from openslides_backend.shared.patterns import (
    collection_from_fqid,
    fqid_from_collection_and_id,
)
from tests.database.writer.system.util import (
    assert_model,
    assert_no_db_entry,
    create_model,
    create_write_requests,
    get_data,
)


def base_test_create_model(
    db_connection: Connection, data: list[dict[str, Any]]
) -> None:
    ids = create_model(data)
    for request_data in data:
        for id_, event in zip(ids, request_data["events"]):
            if not (fqid := event.get("fqid")):
                fqid = fqid_from_collection_and_id(event["collection"], id_)
            event["fields"]["id"] = id_
            assert_model(fqid, event["fields"])


def test_create_simple(db_connection: Connection) -> None:
    base_test_create_model(db_connection, get_data())
    with db_connection.cursor() as curs:
        curs.execute("""SELECT last_value, is_called FROM user_t_id_seq;""")
        assert curs.fetchone() == {"is_called": False, "last_value": 1}


def test_create_collection(db_connection: Connection) -> None:
    data = get_data()
    event = data[0]["events"][0]
    event["collection"] = collection_from_fqid(event.pop("fqid"))
    base_test_create_model(db_connection, data)
    with db_connection.cursor() as curs:
        curs.execute("""SELECT last_value, is_called FROM user_t_id_seq;""")
        assert curs.fetchone() == {"is_called": True, "last_value": 1}


def test_create_twice(db_connection: Connection) -> None:
    data = get_data()
    data.append(data[0])

    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(ModelExists) as e_info:
            extended_database.write(create_write_requests(data))
    assert "user/1" == e_info.value.fqid
    assert_no_db_entry(db_connection.cursor())


def test_create_empty_field(db_connection: Connection) -> None:
    data = get_data({"last_name": None})
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))[0]
    assert_model("user/1", {"id": 1, "username": "1", "first_name": "1"})
