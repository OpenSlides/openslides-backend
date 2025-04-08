from typing import Any
from unittest.mock import MagicMock

import pytest
from psycopg import Connection

from openslides_backend.services.database.commands import GetManyRequest
from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import InvalidFormat
from tests.database.reader.system.util import setup_data, standard_responses

data: dict[str, dict[int, Any]] = {
    "user": {
        1: {
            "id": 1,
            "username": "data",
            "default_vote_weight": "42.000000",
            "meeting_ids": [1, 2, 3],
            "is_demo_user": True,
        },
    },
    "committee": {
        1: {
            "name": "23",
        },
        2: {
            "name": "42",
        },
    },
}
default_request = [
    GetManyRequest("user", [1], ["username"]),
    GetManyRequest("committee", [1, 2], ["name", "organization_id"]),
]
full_request = [
    GetManyRequest("user", [1]),
    GetManyRequest("committee", [1, 2]),
]
default_response = {
    "user": {1: {"id": 1, "username": "data"}},
    "committee": {
        1: {
            "id": 1,
            "name": "23",
            "organization_id": 1,
        },
        2: {
            "id": 2,
            "name": "42",
            "organization_id": 1,
        },
    },
}


def test_simple(db_connection: Connection) -> None:
    setup_data(db_connection, data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get_many(full_request, use_changed_models=False)
    assert response == standard_responses


def test_invalid_fqids(db_connection: Connection) -> None:
    setup_data(db_connection, data)
    request = [
        GetManyRequest("user", [1]),
        GetManyRequest("committee", [1, 4]),
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get_many(request, use_changed_models=False)
    assert response == {
        "user": standard_responses["user"],
        "committee": {1: standard_responses["committee"][1]},
    }


def test_only_invalid_fqids(db_connection: Connection) -> None:
    setup_data(db_connection, data)
    request = [
        GetManyRequest("user", [2]),
        GetManyRequest("committee", [3, 4]),
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get_many(request, use_changed_models=False)
    assert response == {"user": {}, "committee": {}}


def test_mapped_fields(db_connection: Connection) -> None:
    setup_data(db_connection, data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get_many(default_request, use_changed_models=False)
    assert response == default_response


def test_partial_mapped_fields(db_connection: Connection) -> None:
    setup_data(db_connection, data)
    request = [
        GetManyRequest("user", [1], ["username"]),
        GetManyRequest("committee", [2, 1]),
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get_many(request, use_changed_models=False)
    assert response == {
        "user": {1: {"id": 1, "username": "data"}},
        "committee": standard_responses["committee"],
    }


def test_same_collection(db_connection: Connection) -> None:
    setup_data(db_connection, data)
    request = [
        GetManyRequest("committee", [1], ["name"]),
        GetManyRequest("committee", [2], ["name"]),
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get_many(request, use_changed_models=False)
    assert response == {
        "committee": {1: {"id": 1, "name": "23"}, 2: {"id": 2, "name": "42"}},
    }


def test_same_model(db_connection: Connection) -> None:
    setup_data(db_connection, data)
    request = [
        GetManyRequest("committee", [1], ["name"]),
        GetManyRequest("committee", [1], ["organization_id"]),
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get_many(request, use_changed_models=False)
    assert response == {
        "committee": {
            1: {"id": 1, "name": "23", "organization_id": 1},
        },
    }


def test_field_not_exists(db_connection: Connection) -> None:
    setup_data(db_connection, data)
    request = [
        GetManyRequest("committee", [1], ["does_not_exist"]),
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.get_many(request, use_changed_models=False)
    assert (
        "Field 'does_not_exist' does not exist in collection 'committee': column "
        in e_info.value.msg
    )
    assert "does_not_exist" in e_info.value.msg


def test_negative_id(db_connection: Connection) -> None:
    request = [
        GetManyRequest("committee", [-1], ["name"]),
        GetManyRequest("committee", [1], ["organization_id"]),
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.get_many(request, use_changed_models=False)
    assert "Id must be positive." in e_info.value.msg


def test_invalid_collection(db_connection: Connection) -> None:
    request = [
        GetManyRequest("committeee", [1], ["name"]),
        GetManyRequest("committee", [1], ["organization_id"]),
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.get_many(request, use_changed_models=False)
    assert (
        "Collection 'committeee' does not exist in the database: relation"
        in e_info.value.msg
    )


def test_use_changed_models_missing_field(db_connection: Connection) -> None:
    setup_data(db_connection, data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.changed_models["committee/1"].update({"name": "3"})
        response = extended_database.get_many(default_request, use_changed_models=True)
    assert response == {
        "user": {1: {"id": 1, "username": "data"}},
        "committee": {
            1: {"id": 1, "name": "3", "organization_id": 1},
            2: {"id": 2, "name": "42", "organization_id": 1},
        },
    }
