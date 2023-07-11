from collections import defaultdict
from typing import Any, Dict, List, cast

import fastjsonschema

from openslides_backend.shared.mixins.user_scope_mixin import UserScopeMixin
from openslides_backend.shared.schema import id_list_schema

from ..models.models import Committee
from ..services.datastore.commands import GetManyRequest
from ..shared.exceptions import PresenterException
from ..shared.filters import And, FilterOperator, Or
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
        result: Dict[int, Any] = {}
        cml_fields = [
            f"committee_${cml_field}_management_level"
            for cml_field in cast(
                List[str], Committee.user__management_level.replacement_enum
            )
        ]
        gmr = GetManyRequest(
            "user",
            self.data["user_ids"],
            [
                "id",
                "organization_management_level",
                "meeting_ids",
                "committee_ids",
                "committee_$_management_level",
                *cml_fields,
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

    def get_committees_data(self, user: Dict[str, Any]) -> List[Dict[str, Any]]:
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
        for level in user.get("committee_$_management_level", []):
            for committee_nr in user.get(f"committee_${level}_management_level", []):
                if committee_nr in committees:
                    committees[committee_nr]["cml"].append(level)
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

    def get_meetings_data(self, user: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not user.get("meeting_ids"):
            return []

        gmr = GetManyRequest(
            "meeting",
            user["meeting_ids"],
            ["id", "name", "is_active_in_organization_id"],
        )
        meetings = self.datastore.get_many([gmr]).get("meeting", {}).values()

        filter = And(
            Or(
                FilterOperator("meeting_id", "=", meeting_id)
                for meeting_id in user["meeting_ids"]
            ),
            FilterOperator("user_id", "=", user["id"]),
        )
        models_by_meeting: Dict[int, Dict[str, List[int]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for collection in ("motion_submitter", "assignment_candidate", "speaker"):
            models = self.datastore.filter(collection, filter, ["id", "meeting_id"])
            for id, model in models.items():
                models_by_meeting[model["meeting_id"]][f"{collection}_ids"].append(id)

        return [
            {
                "id": meeting["id"],
                "name": meeting.get("name"),
                "is_active_in_organization_id": meeting.get(
                    "is_active_in_organization_id"
                ),
                **models_by_meeting[meeting["id"]],
            }
            for meeting in meetings
        ]
