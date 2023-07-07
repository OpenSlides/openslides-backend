from typing import Any, Dict, List, cast

import fastjsonschema

from openslides_backend.shared.mixins.user_scope_mixin import UserScopeMixin
from openslides_backend.shared.schema import id_list_schema

from ..models.models import Committee
from ..services.datastore.commands import GetManyRequest
from ..shared.exceptions import PresenterException
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
        result: Dict[str, Any] = {}
        for user_id in self.data["user_ids"]:
            self.check_permissions_for_scope(user_id)
            result[str(user_id)] = {}
            committees_data = self.get_committees_data(user_id)
            meetings_data = self.get_meetings_data(user_id)
            if committees_data:
                result[str(user_id)]["committees"] = committees_data
            if meetings_data:
                result[str(user_id)]["meetings"] = meetings_data
        return result

    def get_committees_data(self, user_id: int) -> List[Dict[str, Any]]:
        committees_data = []
        cml_fields = [
            f"committee_${cml_field}_management_level"
            for cml_field in cast(
                List[str], Committee.user__management_level.replacement_enum
            )
        ]
        user = self.datastore.get(
            fqid_from_collection_and_id("user", user_id),
            ["committee_ids", "committee_$_management_level", *cml_fields],
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
            submitter_ids = self.datastore.filter("motion_submitter", filter_, ["id"])
            candidate_ids = self.datastore.filter(
                "assignment_candidate", filter_, ["id"]
            )
            speaker_ids = self.datastore.filter("speaker", filter_, ["id"])
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
