from typing import Any, Dict, List

import fastjsonschema

from ..permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ..permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
    has_perm,
)
from ..permissions.permissions import Permissions
from ..services.datastore.commands import GetManyRequest
from ..shared.exceptions import MissingPermission, PresenterException
from ..shared.filters import And, FilterOperator
from ..shared.patterns import fqid_from_collection_and_id
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
        result: Dict[str, Any] = {}
        for user_id in self.data["user_ids"]:
            result[str(user_id)] = {}
            committees_data = self.get_committees_data(user_id)
            meetings_data = self.get_meetings_data(user_id)
            if committees_data:
                result[str(user_id)]["committees"] = committees_data
            if meetings_data:
                result[str(user_id)]["meetings"] = meetings_data
        self.check_permissions(result)
        return result

    def check_permissions(self, result: Any) -> None:
        """It first collects the meetings which are included and checks them."""
        if has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            return
        for user_id in result:
            meeting_ids = []
            for meeting in result[user_id].get("meetings", []):
                meeting_ids.append(meeting["id"])
            if not all(
                has_perm(
                    self.datastore,
                    self.user_id,
                    Permissions.User.CAN_MANAGE,
                    meeting_id,
                )
                for meeting_id in meeting_ids
            ):
                raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_USERS)
            committee_ids = []
            for committee in result[user_id].get("committees", []):
                committee_ids.append(committee["id"])
            if not all(
                has_committee_management_level(
                    self.datastore,
                    self.user_id,
                    CommitteeManagementLevel.CAN_MANAGE,
                    committee_id,
                )
                for committee_id in committee_ids
            ):
                raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_USERS)

    def get_committees_data(self, user_id: int) -> List[Dict[str, Any]]:
        committees_data = []
        user = self.datastore.get(
            fqid_from_collection_and_id("user", user_id),
            ["committee_ids", "committee_management_ids"],
        )
        if not user.get("committee_ids"):
            return []
        gmr = GetManyRequest("committee", user["committee_ids"], ["id", "name"])
        committees = {
            committee["id"]: {"name": committee.get("name", ""), "cml": []}
            for committee in self.datastore.get_many([gmr])
            .get("committee", {})
            .values()
        }
        for committee_nr in user.get("committee_management_ids", []):
            if committee_nr in committees:
                committees[committee_nr]["cml"].append("can_manage")
            else:
                raise PresenterException(
                    f"Data error: user has rights for committee {committee_nr}, but faultily is no member of committee."
                )
        for committee_id, committee in committees.items():
            committees_data.append(
                {
                    "id": committee_id,
                    "name": committee.get("name", ""),
                    "cml": ", ".join(committee.get("cml", [])),
                }
            )
        return committees_data

    def get_meetings_data(self, user_id: int) -> List[Dict[str, Any]]:
        meetings_data = []
        user = self.datastore.get(
            fqid_from_collection_and_id("user", user_id), ["meeting_ids"]
        )
        if not user.get("meeting_ids"):
            return []
        gmr = GetManyRequest(
            "meeting",
            user["meeting_ids"],
            ["id", "name", "is_active_in_organization_id"],
        )
        meetings = self.datastore.get_many([gmr]).get("meeting", {}).values()
        for meeting in meetings:
            filter_ = And(
                FilterOperator("meeting_id", "=", meeting["id"]),
                FilterOperator("user_id", "=", user_id),
            )
            meeting_users = self.datastore.filter(
                "meeting_user",
                filter_,
                ["speaker_ids", "submitted_motion_ids", "assignment_candidate_ids"],
            )
            speaker_ids = []
            submitter_ids = []
            candidate_ids = []
            if meeting_users:
                meeting_user = list(meeting_users.values())[0]
                speaker_ids = meeting_user.get("speaker_ids", [])
                submitter_ids = meeting_user.get("submitted_motion_ids", [])
                candidate_ids = meeting_user.get("assignment_candidate_ids", [])
            if submitter_ids or candidate_ids or speaker_ids:
                meetings_data.append(
                    {
                        "id": meeting["id"],
                        "name": meeting.get("name"),
                        "is_active_in_organization_id": meeting.get(
                            "is_active_in_organization_id"
                        ),
                        "submitter_ids": submitter_ids,
                        "candidate_ids": candidate_ids,
                        "speaker_ids": speaker_ids,
                    }
                )
        return meetings_data
