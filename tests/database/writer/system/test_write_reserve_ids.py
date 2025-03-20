from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.database.interface import COLLECTION_MAX_LEN
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import InvalidFormat
from openslides_backend.shared.patterns import collection_from_fqid
from tests.database.writer.system.util import create_model, get_data


@pytest.fixture(autouse=True)
def reset_ids_on_teardown(db_connection: Connection) -> Generator:
    yield "Halt until test finishes."
    data = get_data()
    for request in data:
        for event in request["events"]:
            if fqid := event.get("fqid"):
                table_name = collection_from_fqid(fqid) + "_t"
            else:
                table_name = event["collection"] + "_t"
            with db_connection.cursor() as curs:
                curs.execute(
                    "INSERT INTO truncate_tables (tablename) VALUES(%s)", (table_name,)
                )


def test_single(db_connection: Connection) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        assert extended_database.reserve_ids("user", 1) == [1]
    with db_connection.cursor() as curs:
        curs.execute("""SELECT last_value, is_called FROM user_t_id_seq;""")
        assert curs.fetchone() == {"is_called": True, "last_value": 1}


def test_multiple(db_connection: Connection) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        assert extended_database.reserve_ids("user", 3) == [1, 2, 3]
    with db_connection.cursor() as curs:
        curs.execute("""SELECT last_value, is_called FROM user_t_id_seq;""")
        assert curs.fetchone() == {"is_called": True, "last_value": 3}


def test_successive(db_connection: Connection) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        assert extended_database.reserve_ids("user", 3) == [1, 2, 3]
        assert extended_database.reserve_ids("user", 3) == [4, 5, 6]
    with db_connection.cursor() as curs:
        curs.execute("""SELECT last_value, is_called FROM user_t_id_seq;""")
        assert curs.fetchone() == {"is_called": True, "last_value": 6}


def test_wrong_format(db_connection: Connection) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.reserve_ids("user", None)  # type:ignore
    assert e_info.value.msg == ("Amount must be integer.")


def test_negative_amount(db_connection: Connection) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.reserve_ids("user", -1)
    assert e_info.value.msg == ("Amount must be >= 1, not -1.")


def test_zero(db_connection: Connection) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.reserve_ids("user", 0)
    assert e_info.value.msg == ("Amount must be >= 1, not 0.")


def test_too_long_collection(db_connection: Connection) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.reserve_ids("x" * (COLLECTION_MAX_LEN + 1), 2)
    assert e_info.value.msg == (
        f"Collection length must be between 1 and {COLLECTION_MAX_LEN}"
    )


def test_create_reserve(db_connection: Connection) -> None:
    data = get_data()
    create_model(data)

    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        assert extended_database.reserve_ids("user", 2) == [2, 3]

    with db_connection.cursor() as curs:
        curs.execute("""SELECT last_value, is_called FROM user_t_id_seq;""")
        assert curs.fetchone() == {"is_called": True, "last_value": 3}


def test_reserve_create(db_connection: Connection) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        assert extended_database.reserve_ids("user", 5) == [1, 2, 3, 4, 5]

    with db_connection.cursor() as curs:
        curs.execute("""SELECT last_value, is_called FROM user_t_id_seq;""")
        assert curs.fetchone() == {"is_called": True, "last_value": 5}
    create_model(get_data())
    with db_connection.cursor() as curs:
        curs.execute("""SELECT last_value, is_called FROM user_t_id_seq;""")
        assert curs.fetchone() == {"is_called": True, "last_value": 6}
