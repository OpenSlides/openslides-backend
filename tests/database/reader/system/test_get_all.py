from unittest.mock import MagicMock

import pytest
from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import InvalidFormat
from tests.database.reader.system.util import (
    setup_data,
    standard_data,
    standard_responses,
)


def test_simple(db_connection: Connection) -> None:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get_all("committee")
    assert response == standard_responses["committee"]


def test_mapped_fields(db_connection: Connection) -> None:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get_all("committee", ["name", "id"])
    assert response == {
        1: {
            "id": 1,
            "name": "23",
        },
        2: {
            "id": 2,
            "name": "42",
        },
    }


def test_invalid_collection() -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.get_all("commite", ["name", "id"])
    assert (
        "Collection 'commite' does not exist in the database: relation"
        in e_info.value.message
    )


def test_invalid_mapped_fields() -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.get_all("committee", ["id", "nam", "organization_id"])
    assert (
        "Field 'nam' does not exist in collection 'committee': column"
        in e_info.value.message
    )
