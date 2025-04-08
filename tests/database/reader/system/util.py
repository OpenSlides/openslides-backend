import json
from decimal import Decimal
from typing import Any

from psycopg import Connection

from openslides_backend.shared.patterns import strip_reserved_fields

standard_responses = {
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
            "email": None,
            "default_vote_weight": Decimal("42.000000"),
            "last_email_sent": None,
            "is_demo_user": True,
            "last_login": None,
            "organization_management_level": None,
            "meeting_ids": [1, 2, 3],
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
        }
    },
    "committee": {
        1: {
            "id": 1,
            "name": "23",
            "description": None,
            "external_id": None,
            "default_meeting_id": None,
            "forward_to_committee_ids": None,
            "manager_ids": None,
            "meeting_ids": None,
            "organization_tag_ids": None,
            "receive_forwardings_from_committee_ids": None,
            "user_ids": None,
            "organization_id": 1,
        },
        2: {
            "id": 2,
            "name": "42",
            "description": None,
            "external_id": None,
            "default_meeting_id": None,
            "forward_to_committee_ids": None,
            "manager_ids": None,
            "meeting_ids": None,
            "organization_id": 1,
            "organization_tag_ids": None,
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
