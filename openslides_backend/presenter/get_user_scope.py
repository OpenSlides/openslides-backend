from enum import Enum
from typing import Any, Dict, Tuple, cast

import fastjsonschema

from ..services.datastore.commands import GetManyRequest
from ..shared.patterns import Collection, FullQualifiedId
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

get_user_scope_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "get_user_related_models",
        "description": "get user ids related models",
        "properties": {
            "user_ids": {
                "type": "array",
                "item": {"type": "integer"},
            },
        },
        "required": ["user_ids"],
        "additionalProperties": False,
    }
)


class UserScope(int, Enum):
    Meeting = 1
    Committee = 2
    Organization = 3


@register_presenter("get_user_scope")
class GetUserScope(BasePresenter):
    """
    Gets for the user_ids the user scope.
    """

    schema = get_user_scope_schema

    def get_result(self) -> Any:
        result: Dict["str", Any] = {}
        user_ids = self.data["user_ids"]
        for user_id in user_ids:
            scope, scope_id = self.get_user_scope(user_id)
            if scope == UserScope.Committee:
                scope_str = "committee"
            elif scope == UserScope.Organization:
                scope_str = "organization"
            else:
                scope_str = "meeting"
            result[str(user_id)] = {"collection": scope_str, "id": scope_id}
        return result

    def get_user_scope(self, user_id: int) -> Tuple[UserScope, int]:
        user = self.datastore.fetch_model(
            FullQualifiedId(Collection("user"), user_id),
            ["meeting_ids", "committee_$_management_level"],
        )
        meetings = user.get("meeting_ids", [])
        committees_manager = set(map(int, user.get("committee_$_management_level", [])))
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    Collection("meeting"),
                    meetings,
                    ["committee_id", "is_active_in_organization_id"],
                )
            ]
        ).get(Collection("meeting"), {})
        committees_of_meetings = set(
            meeting_data.get("committee_id")
            for _, meeting_data in result.items()
            if meeting_data.get("is_active_in_organization_id")
        )
        committees = list(committees_manager | committees_of_meetings)
        meetings_committee = {
            meeting_id: meeting_data.get("committee_id")  # type: ignore
            for meeting_id, meeting_data in result.items()
            if meeting_data.get("is_active_in_organization_id")
        }

        if len(meetings_committee) == 1 and len(committees) == 1:
            return UserScope.Meeting, next(iter(meetings_committee))
        elif len(committees) == 1:
            return UserScope.Committee, cast(int, committees[0])
        return UserScope.Organization, 1
