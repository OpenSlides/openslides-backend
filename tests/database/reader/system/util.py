import json
from datetime import datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from psycopg import Connection

from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.patterns import strip_reserved_fields

standard_data: dict[str, dict[int, Any]] = {
    "user": {
        1: {
            "id": 1,
            "username": "data",
            "default_vote_weight": "42.000000",
            "is_demo_user": True,
            "last_login": "2042/11/19 9:53:20",
        },
        2: {
            "id": 2,
            "username": "daren",
            "first_name": "daren",
            "last_name": "nerad",
            "last_login": "2012/05/31",
            "default_vote_weight": "23.000000",
            "is_demo_user": False,
        },
        3: {
            "id": 3,
            "username": "3",
            "first_name": "nerad",
            "default_vote_weight": "81.000000",
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

standard_responses: dict[str, dict[int, dict[str, Any]]] = {
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
            "gender_id": None,
            "external": None,
            "home_committee_id": None,
            "email": None,
            "default_vote_weight": Decimal("42"),
            "last_email_sent": None,
            "is_demo_user": True,
            "last_login": datetime(2042, 11, 19, 9, 53, 20, tzinfo=ZoneInfo("UTC")),
            "organization_management_level": None,
            "meeting_ids": None,
            "is_present_in_meeting_ids": None,
            "meeting_user_ids": None,
            "option_ids": None,
            "poll_candidate_ids": None,
            "poll_voted_ids": None,
            "vote_ids": None,
            "committee_ids": None,
            "committee_management_ids": None,
            "delegated_vote_ids": None,
            "organization_id": 1,
        },
        2: {
            "id": 2,
            "username": "daren",
            "member_number": None,
            "saml_id": None,
            "pronoun": None,
            "title": None,
            "first_name": "daren",
            "last_name": "nerad",
            "is_active": True,
            "is_physical_person": True,
            "password": None,
            "default_password": None,
            "can_change_own_password": True,
            "gender_id": None,
            "external": None,
            "home_committee_id": None,
            "email": None,
            "default_vote_weight": Decimal("23"),
            "last_email_sent": None,
            "is_demo_user": False,
            "last_login": datetime(2012, 5, 31, 0, 0, tzinfo=ZoneInfo("UTC")),
            "organization_management_level": None,
            "meeting_ids": None,
            "is_present_in_meeting_ids": None,
            "meeting_user_ids": None,
            "option_ids": None,
            "poll_candidate_ids": None,
            "poll_voted_ids": None,
            "vote_ids": None,
            "committee_ids": None,
            "committee_management_ids": None,
            "delegated_vote_ids": None,
            "organization_id": 1,
        },
        3: {
            "id": 3,
            "username": "3",
            "member_number": None,
            "saml_id": None,
            "pronoun": None,
            "title": None,
            "first_name": "nerad",
            "last_name": None,
            "is_active": True,
            "is_physical_person": True,
            "password": None,
            "default_password": None,
            "can_change_own_password": True,
            "gender_id": None,
            "external": None,
            "home_committee_id": None,
            "email": None,
            "default_vote_weight": Decimal("81"),
            "last_email_sent": None,
            "is_demo_user": True,
            "last_login": None,
            "organization_management_level": None,
            "meeting_ids": None,
            "is_present_in_meeting_ids": None,
            "meeting_user_ids": None,
            "option_ids": None,
            "poll_candidate_ids": None,
            "poll_voted_ids": None,
            "vote_ids": None,
            "committee_ids": None,
            "committee_management_ids": None,
            "delegated_vote_ids": None,
            "organization_id": 1,
        },
    },
    "committee": {
        1: {
            "all_child_ids": None,
            "all_parent_ids": None,
            "child_ids": None,
            "id": 1,
            "name": "23",
            "description": None,
            "external_id": None,
            "default_meeting_id": None,
            "forward_to_committee_ids": None,
            "manager_ids": None,
            "meeting_ids": None,
            "native_user_ids": None,
            "organization_tag_ids": None,
            "parent_id": None,
            "receive_forwardings_from_committee_ids": None,
            "user_ids": None,
            "organization_id": 1,
        },
        2: {
            "all_child_ids": None,
            "all_parent_ids": None,
            "child_ids": None,
            "id": 2,
            "name": "42",
            "description": None,
            "external_id": None,
            "default_meeting_id": None,
            "forward_to_committee_ids": None,
            "manager_ids": None,
            "meeting_ids": None,
            "native_user_ids": None,
            "organization_id": 1,
            "organization_tag_ids": None,
            "parent_id": None,
            "receive_forwardings_from_committee_ids": None,
            "user_ids": None,
        },
    },
}


def setup_data(connection: Connection, data: dict[str, dict[int, Any]]) -> None:
    with connection.cursor() as cursor:
        for collection, models in data.items():
            for model in models.values():
                model_data = json.loads(json.dumps(model))
                strip_reserved_fields(model_data)
                cursor.execute(
                    f"INSERT INTO {collection}_t ({', '.join(key for key in model_data.keys())}) VALUES ({', '.join('%s' for i in range(len(model_data)))})",
                    [val for val in model_data.values()],
                )
    connection.commit()


def insert_into_intermediate_table(
    table: str, columns: list[str], data: list[tuple[int, int]]
) -> None:
    with get_new_os_conn() as connection:
        with connection.cursor() as cursor:
            for values in data:
                cursor.execute(
                    f"INSERT INTO {table} ({', '.join(columns)}) VALUES {values}"
                )
