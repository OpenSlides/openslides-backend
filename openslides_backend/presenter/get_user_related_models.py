from typing import Any

import fastjsonschema

from openslides_backend.shared.mixins.user_scope_mixin import UserScopeMixin
from openslides_backend.shared.schema import id_list_schema

from ..services.database.commands import GetManyRequest
from ..shared.exceptions import PresenterException
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
            "user_ids": id_list_schema,
        },
        "required": ["user_ids"],
        "additionalProperties": False,
    }
)


@register_presenter("get_user_related_models")
class GetUserRelatedModels(UserScopeMixin, BasePresenter):
    """
    Collects related models of the user_ids.
    """

    schema = get_user_related_models_schema

    def get_result(self) -> Any:
        result: dict[int, Any] = {}
        gmr = GetManyRequest(
            "user",
            self.data["user_ids"],
            [
                "id",
                "organization_management_level",
                "meeting_user_ids",
                "committee_ids",
                "committee_management_ids",
            ],
        )
        users = self.datastore.get_many([gmr]).get("user", {})
        for user_id, user in users.items():
            result[user_id] = {}
            self.check_permissions_for_scope(user_id)
            if oml := user.get("organization_management_level"):
                result[user_id]["organization_management_level"] = oml
            if committees_data := self.get_committees_data(user):
                result[user_id]["committees"] = committees_data
            if meetings_data := self.get_meetings_data(user):
                result[user_id]["meetings"] = meetings_data
        return result

    def get_committees_data(self, user: dict[str, Any]) -> list[dict[str, Any]]:
        if not user.get("committee_ids"):
            return []

        committees_data = []
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

    def get_meetings_data(self, user: dict[str, Any]) -> list[dict[str, Any]]:
        if not (meeting_user_ids := user.get("meeting_user_ids")):
            return []

        result_fields = (
            "speaker_ids",
            "motion_submitter_ids",
            "assignment_candidate_ids",
            "locked_out",
        )
        meeting_users = [
            meeting_user
            for meeting_user in self.datastore.get_many(
                [
                    GetManyRequest(
                        "meeting_user",
                        meeting_user_ids,
                        [*result_fields, "group_ids", "meeting_id"],
                    )
                ]
            )["meeting_user"].values()
            if meeting_user.pop("group_ids", None)
        ]

        if len(meeting_users) == 0:
            return []

        gmr = GetManyRequest(
            "meeting",
            [meeting_user["meeting_id"] for meeting_user in meeting_users],
            ["id", "name", "is_active_in_organization_id", "locked_from_inside"],
        )
        meetings = self.datastore.get_many([gmr]).get("meeting", {})
        operator_meetings = self.datastore.get(
            fqid_from_collection_and_id("user", self.user_id),
            ["meeting_ids"],
            lock_result=False,
        ).get("meeting_ids", [])

        return [
            {
                "id": meeting["id"],
                "name": meeting.get("name"),
                "is_active_in_organization_id": meeting.get(
                    "is_active_in_organization_id"
                ),
                "is_locked": meeting.get("locked_from_inside", False),
                **{
                    field: value
                    for field in result_fields
                    if (value := meeting_user.get(field))
                    and (
                        not meeting.get("locked_from_inside")
                        or meeting["id"] in operator_meetings
                    )
                },
            }
            for meeting_user in meeting_users
            if (meeting := meetings.get(meeting_user["meeting_id"]))
        ]
