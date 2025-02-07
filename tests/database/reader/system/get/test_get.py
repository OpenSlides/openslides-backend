from decimal import Decimal

import pytest
from psycopg import Connection, Cursor

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.shared.exceptions import (
    BadCodingException,
    DatabaseException,
    InvalidFormat,
)
from tests.database.reader.system.util import setup_data

ID = 1
COLLECTION = "user"
FQID = f"{COLLECTION}/{ID}"
data = {
    COLLECTION: {
        str(ID): {
            "id": ID,
            "username": "data",
            "default_vote_weight": "42.000000",
            "meeting_ids": [1, 2, 3],
            "is_demo_user": True,
        },
    },
}
standard_response = {
    "id": ID,
    "username": "data",
    "member_number": None,
    "saml_id": None,
    "pronoun": None,
    "title": None,
    "first_name": None,
    "last_name": None,
    "is_active": True,
    "is_physical_person": True,
    "password": None,
    "default_password": None,
    "can_change_own_password": True,
    "gender": None,
    "email": None,
    "default_vote_weight": Decimal("42"),
    "last_email_sent": None,
    "is_demo_user": True,
    "last_login": None,
    "organization_management_level": None,
    "meeting_ids": [1, 2, 3],
    "organization_id": 1,
}


def test_simple(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    setup_data(db_connection, db_cur, data)
    response = reader.get(FQID)
    assert response == standard_response


def test_no_model(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    response = reader.get("motion/111")
    assert response == {}


def test_no_collection(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    with pytest.raises(InvalidFormat) as e_info:
        reader.get("doesntexist/1")
    assert "The collection does not exist in the database" in e_info.value.msg


def test_mapped_fields(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    setup_data(db_connection, db_cur, data)
    response = reader.get(FQID, ["id", "username"])
    assert response == {
        "id": ID,
        "username": "data",
    }


def test_too_many_mapped_fields(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    """The reader should return just all fields."""
    setup_data(db_connection, db_cur, data)
    fields = [f"field_{i}" for i in range(2000)]
    response = reader.get(FQID, fields)
    assert response == standard_response


def test_mapped_fields_not_exists(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    setup_data(db_connection, db_cur, data)
    with pytest.raises(InvalidFormat) as e_info:
        reader.get(FQID, ["field_that_doesnt_exist"])
    assert "A field does not exist in model table: " in e_info.value.msg


def test_invalid_fqid(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    with pytest.raises(InvalidFormat) as e_info:
        reader.get("not valid")
    assert "Invalid fqid format. list index out of range" == e_info.value.msg


def test_invalid_mapped_fields(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    with pytest.raises(DatabaseException) as e_info:
        reader.get(FQID, ["not valid"])
    assert "Invalid fields: ['not valid']" == e_info.value.msg


def test_invalid_mapped_fields2(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    """This should never happen as per the type annotations, but you never know."""
    with pytest.raises(DatabaseException) as e_info:
        reader.get(FQID, [None])  # type: ignore
    assert "Invalid fields: [None]" in e_info.value.msg


def test_none(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    """This should never happen as per the type annotations, but you never know."""
    with pytest.raises(BadCodingException) as e_info:
        reader.get(None)  # type: ignore
    assert "No fqid. Offer at least one fqid." == e_info.value.message
