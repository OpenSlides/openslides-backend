from typing import Any, Dict, List

import fastjsonschema

from ..permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ..permissions.permission_helper import has_organization_management_level
from ..services.datastore.commands import GetManyRequest
from ..shared.exceptions import MissingPermission
from ..shared.filters import And, FilterOperator
from ..shared.patterns import Collection, FullQualifiedId
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

get_user_related_models_schema = fastjsonschema.compile(
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


@register_presenter("get_user_related_models")
class GetUserRelatedModels(BasePresenter):
    """
    Collects related models of the user_ids.
    """

    schema = get_user_related_models_schema

    def get_result(self) -> Any:
        self.check_permissions()
        result: Dict[str, Any] = {}
        for user_id in self.data["user_ids"]:
            result[str(user_id)] = {}
            committees_data = self.get_committees_data(user_id)
            meetings_data = self.get_meetings_data(user_id)
            if committees_data:
                result[str(user_id)]["committees"] = committees_data
            if meetings_data:
                result[str(user_id)]["meetings"] = meetings_data
        return result

    def check_permissions(self) -> None:
        if not has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_USERS)

    def get_committees_data(self, user_id: int) -> List[Dict[str, Any]]:
        committees = []
        user = self.datastore.get(
            FullQualifiedId(Collection("user"), user_id), ["committee_ids"]
        )
        return_committees = False
        for committee_id in user.get("committee_ids", []):
            user2 = self.datastore.get(
                FullQualifiedId(Collection("user"), user_id),
                [f"committee_${committee_id}_management_level"],
            )
            if (
                CommitteeManagementLevel(
                    user2.get(f"committee_${committee_id}_management_level")
                )
                >= CommitteeManagementLevel.CAN_MANAGE
            ):
                return_committees = True

            committee = self.datastore.get(
                FullQualifiedId(Collection("committee"), committee_id), ["name"]
            )
            committees.append(
                {
                    "id": committee_id,
                    "name": committee.get("name", ""),
                    "cml": user2.get(f"committee_${committee_id}_management_level", ""),
                }
            )
        if return_committees:
            return committees
        return []

    def get_meetings_data(self, user_id: int) -> List[Dict[str, Any]]:
        meetings_data = []
        user = self.datastore.get(
            FullQualifiedId(Collection("user"), user_id), ["meeting_ids"]
        )
        if not user.get("meeting_ids"):
            return []
        gmr = GetManyRequest(
            Collection("meeting"),
            user["meeting_ids"],
            ["id", "name", "is_active_in_organization_id"],
        )
        meetings = (
            self.datastore.get_many([gmr]).get(Collection("meeting"), {}).values()
        )
        for meeting in meetings:
            filter_ = And(
                FilterOperator("meeting_id", "=", meeting["id"]),
                FilterOperator("user_id", "=", user_id),
            )
            submitter_ids = self.datastore.filter(
                Collection("motion_submitter"), filter_
            )
            candidate_ids = self.datastore.filter(
                Collection("assignment_candidate"), filter_
            )
            speaker_ids = self.datastore.filter(Collection("speaker"), filter_)
            if submitter_ids or candidate_ids or speaker_ids:
                meetings_data.append(
                    {
                        "id": meeting["id"],
                        "name": meeting.get("name"),
                        "is_active_in_organization_id": meeting.get(
                            "is_active_in_organization_id"
                        ),
                        "submitter_ids": list(submitter_ids),
                        "candidate_ids": list(candidate_ids),
                        "speaker_ids": list(speaker_ids),
                    }
                )
        return meetings_data
