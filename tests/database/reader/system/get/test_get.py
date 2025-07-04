from unittest.mock import MagicMock

import pytest
from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import (
    BadCodingException,
    InvalidFormat,
    ModelDoesNotExist,
)
from openslides_backend.shared.typing import DeletedModel
from tests.database.reader.system.util import (
    setup_data,
    standard_data,
    standard_responses,
)

ID = 1
COLLECTION = "user"
FQID = f"{COLLECTION}/{ID}"
data = {
    COLLECTION: {
        ID: {
            "id": ID,
            "username": "data",
            "default_vote_weight": "42.000000",
            "meeting_ids": [1, 2, 3],
            "is_demo_user": True,
        },
    },
}
standard_response = {
    k: v for k, v in standard_responses["user"][ID].items() if v is not None
}


def test_simple(db_connection: Connection) -> None:
    setup_data(db_connection, data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get(FQID)
    assert response == standard_response


def test_view_field_relation_list_ordered(db_connection: Connection) -> None:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO nm_committee_manager_ids_user (committee_id, user_id) VALUES (2, 1)"
            )
            cursor.execute(
                "INSERT INTO nm_committee_manager_ids_user (committee_id, user_id) VALUES (1, 1)"
            )
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get("user/1")
    assert response["committee_management_ids"] == [1, 2]


def test_no_model(db_connection: Connection) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(ModelDoesNotExist) as e_info:
            extended_database.get("motion/111")
    assert "motion/111" in e_info.value.fqid


def test_no_collection(db_connection: Connection) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.get("doesntexist/1")
    assert (
        "Collection 'doesntexist' does not exist in the database:"
        in e_info.value.message
    )


def test_mapped_fields(db_connection: Connection) -> None:
    setup_data(db_connection, data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get(FQID, ["id", "username"])
    assert response == {
        "id": ID,
        "username": "data",
    }


def test_too_many_mapped_fields(db_connection: Connection) -> None:
    """The reader should return just all fields."""
    setup_data(db_connection, data)
    fields = [f"field_{i}" for i in range(2000)]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get(FQID, fields)
    assert response == standard_response


def test_mapped_fields_not_exists(db_connection: Connection) -> None:
    setup_data(db_connection, data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.get(FQID, ["that_doesnt_exist"])
    assert (
        "Field 'that_doesnt_exist' does not exist in collection 'user': column"
        in e_info.value.message
    )


def test_invalid_fqid(db_connection: Connection) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.get("not valid")
    assert "Invalid fqid format. list index out of range" == e_info.value.message


def test_invalid_mapped_fields(db_connection: Connection) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.get(FQID, ["not valid"])
    assert "Invalid fields: ['not valid']" == e_info.value.message


def test_invalid_mapped_fields2(db_connection: Connection) -> None:
    """This should never happen as per the type annotations, but you never know."""
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.get(FQID, [None])  # type: ignore
    assert "Invalid fields: [None]" in e_info.value.message


def test_none(db_connection: Connection) -> None:
    """This should never happen as per the type annotations, but you never know."""
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(BadCodingException) as e_info:
            extended_database.get(None)  # type: ignore
    assert "No fqid. Offer at least one fqid." == e_info.value.message


def test_changed_models_only(db_connection: Connection) -> None:
    """Requests data from changed models dict only."""
    with get_new_os_conn() as conn:
        ex_db = ExtendedDatabase(conn, MagicMock(), MagicMock())
        ex_db.apply_changed_model(FQID, {"is_demo_user": True})
        response = ex_db.get(FQID, ["is_demo_user"])
    assert response == {"is_demo_user": True, "id": ID}


def test_changed_models_with_db_instance(db_connection: Connection) -> None:
    """Uses data from database and changed models dict."""
    setup_data(db_connection, data)
    with get_new_os_conn() as conn:
        ex_db = ExtendedDatabase(conn, MagicMock(), MagicMock())
        ex_db.apply_changed_model(FQID, {"is_demo_user": True})
        response = ex_db.get(FQID, ["is_demo_user", "username"])
    assert response == {"is_demo_user": True, "username": "data", "id": ID}


def test_changed_models_without_db_instance(db_connection: Connection) -> None:
    """Requests data from changed models dict and database which is not filled."""
    with get_new_os_conn() as conn:
        ex_db = ExtendedDatabase(conn, MagicMock(), MagicMock())
        ex_db.apply_changed_model(FQID, {"is_demo_user": True, "meta_new": True})
        response = ex_db.get(FQID, ["is_demo_user", "username"])
    assert response == {"is_demo_user": True, "id": ID}


@pytest.mark.skip(
    reason="we only raise an exception now if the model is not present in the changed_models at all"
)
def test_changed_models_without_db_instance_fail(db_connection: Connection) -> None:
    """
    Requests data from changed models dict and database which was deleted by another process.
    The similar case where only changed model fields are requested is even trickier.
    """
    with get_new_os_conn() as conn:
        ex_db = ExtendedDatabase(conn, MagicMock(), MagicMock())
        ex_db.apply_changed_model(FQID, {"is_demo_user": True})
        with pytest.raises(ModelDoesNotExist) as e_info:
            ex_db.get(FQID, ["is_demo_user", "username"])
    assert e_info.value.message == "Model 'user/1' does not exist."
    assert e_info.value.fqid == FQID


def test_changed_models_deleted(db_connection: Connection) -> None:
    """Requests an object that was deleted."""
    setup_data(db_connection, data)
    with get_new_os_conn() as conn:
        ex_db = ExtendedDatabase(conn, MagicMock(), MagicMock())
        ex_db.apply_changed_model(FQID, DeletedModel())
        with pytest.raises(ModelDoesNotExist) as e_info:
            ex_db.get(FQID)
    assert e_info.value.message == "Model 'user/1' does not exist."
    assert e_info.value.fqid == FQID
