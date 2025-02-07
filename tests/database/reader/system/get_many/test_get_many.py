from decimal import Decimal

import pytest
from psycopg import Connection, Cursor

from openslides_backend.services.database.commands import GetManyRequest
from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.shared.exceptions import InvalidFormat
from tests.database.reader.system.util import setup_data

data = {
    "user": {
        "1": {
            "id": 1,
            "username": "data",
            "default_vote_weight": "42.000000",
            "meeting_ids": [1, 2, 3],
            "is_demo_user": True,
        },
    },
    "committee": {
        "1": {
            "name": "23",
            "forwarding_user_id": 1,
        },
        "2": {
            "name": "42",
            "forwarding_user_id": 1,
        },
    },
}
default_request = [
    GetManyRequest("user", [1], ["username"]),
    GetManyRequest("committee", [1, 2], ["name", "forwarding_user_id"]),
]
full_request = [
    GetManyRequest("user", [1]),
    GetManyRequest("committee", [1, 2]),
]
default_response = {
    "user": {1: {"id": 1, "username": "data"}},
    "committee": {
        1: {"id": 1, "name": "23", "forwarding_user_id": 1},
        2: {"id": 2, "name": "42", "forwarding_user_id": 1},
    },
}
full_response = {
    "user": {
        1: {
            "id": 1,
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
    },
    "committee": {
        1: {
            "id": 1,
            "name": "23",
            "description": None,
            "external_id": None,
            "default_meeting_id": None,
            "forwarding_user_id": 1,
            "organization_id": 1,
        },
        2: {
            "id": 2,
            "name": "42",
            "description": None,
            "external_id": None,
            "default_meeting_id": None,
            "forwarding_user_id": 1,
            "organization_id": 1,
        },
    },
}


def test_simple(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    setup_data(db_connection, db_cur, data)
    response = reader.get_many(full_request, use_changed_models=False)
    assert response == full_response


def test_invalid_fqids(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    setup_data(db_connection, db_cur, data)
    request = [
        GetManyRequest("user", [1]),
        GetManyRequest("committee", [1, 4]),
    ]
    response = reader.get_many(request, use_changed_models=False)
    assert response == {
        "user": {
            1: {
                "id": 1,
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
        },
        "committee": {
            1: {
                "id": 1,
                "name": "23",
                "description": None,
                "external_id": None,
                "default_meeting_id": None,
                "forwarding_user_id": 1,
                "organization_id": 1,
            },
        },
    }


def test_only_invalid_fqids(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    setup_data(db_connection, db_cur, data)
    request = [
        GetManyRequest("user", [2]),
        GetManyRequest("committee", [3, 4]),
    ]
    response = reader.get_many(request, use_changed_models=False)
    assert response == {"user": {}, "committee": {}}


def test_mapped_fields(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    setup_data(db_connection, db_cur, data)
    response = reader.get_many(default_request, use_changed_models=False)
    assert response == default_response


def test_partial_mapped_fields(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    setup_data(db_connection, db_cur, data)
    request = [
        GetManyRequest("user", [1], ["username"]),
        GetManyRequest("committee", [2, 1]),
    ]
    response = reader.get_many(request, use_changed_models=False)
    assert response == {
        "user": {1: {"id": 1, "username": "data"}},
        "committee": {
            1: {
                "id": 1,
                "name": "23",
                "description": None,
                "external_id": None,
                "default_meeting_id": None,
                "forwarding_user_id": 1,
                "organization_id": 1,
            },
            2: {
                "id": 2,
                "name": "42",
                "description": None,
                "external_id": None,
                "default_meeting_id": None,
                "forwarding_user_id": 1,
                "organization_id": 1,
            },
        },
    }


def test_same_collection(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    setup_data(db_connection, db_cur, data)
    request = [
        GetManyRequest("committee", [1], ["name"]),
        GetManyRequest("committee", [2], ["name"]),
    ]
    response = reader.get_many(request, use_changed_models=False)
    assert response == {
        "committee": {1: {"id": 1, "name": "23"}, 2: {"id": 2, "name": "42"}},
    }


def test_same_model(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    setup_data(db_connection, db_cur, data)
    request = [
        GetManyRequest("committee", [1], ["name"]),
        GetManyRequest("committee", [1], ["forwarding_user_id"]),
    ]
    response = reader.get_many(request, use_changed_models=False)
    assert response == {
        "committee": {
            1: {"id": 1, "name": "23", "forwarding_user_id": 1},
        },
    }


def test_field_not_exists(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    setup_data(db_connection, db_cur, data)
    request = [
        GetManyRequest("committee", [1], ["does_not_exist"]),
    ]
    with pytest.raises(InvalidFormat) as e_info:
        reader.get_many(request, use_changed_models=False)
    assert "A field does not exist in model table: column " in e_info.value.msg
    assert "does_not_exist" in e_info.value.msg


def test_negative_id(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    request = [
        GetManyRequest("committee", [-1], ["name"]),
        GetManyRequest("committee", [1], ["forwarding_user_id"]),
    ]
    with pytest.raises(InvalidFormat) as e_info:
        reader.get_many(request, use_changed_models=False)
    assert "Id must be positive." in e_info.value.msg


def test_invalid_collection(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    request = [
        GetManyRequest("committeee", [1], ["name"]),
        GetManyRequest("committee", [1], ["forwarding_user_id"]),
    ]
    with pytest.raises(InvalidFormat) as e_info:
        reader.get_many(request, use_changed_models=False)
    assert "The collection does not exist in the database: relation" in e_info.value.msg
    assert "committeee_t" in e_info.value.msg


def test_use_changed_models_missing_field(
    db_connection: Connection, db_cur: Cursor, reader: ExtendedDatabase
) -> None:
    setup_data(db_connection, db_cur, data)
    reader.changed_models["committee/1"].update({"name": "3"})
    response = reader.get_many(default_request, use_changed_models=True)
    assert response == {
        "user": {1: {"id": 1, "username": "data"}},
        "committee": {
            1: {"id": 1, "name": "3", "forwarding_user_id": 1},
            2: {"id": 2, "name": "42", "forwarding_user_id": 1},
        },
    }
