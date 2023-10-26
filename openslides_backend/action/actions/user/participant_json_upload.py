from typing import Any, Dict, List, Optional, Union

from openslides_backend.shared.schema import required_id_schema, str_list_schema

from ....models.models import MeetingUser
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ...mixins.import_mixins import ImportState
from ...util.register import register_action
from .base_json_upload import BaseUserJsonUpload


@register_action("participant.json_upload")
class ParticipantJsonUpload(BaseUserJsonUpload):
    schema = BaseUserJsonUpload.get_schema(
        additional_required_fields={
            "meeting_id": required_id_schema,
        },
        additional_user_fields={
            **MeetingUser().get_properties(
                "structure_level",
                "number",
                "vote_weight",
                "comment",
            ),
            "is_present": {"type": "boolean"},
            "groups": str_list_schema,
        },
    )
    headers = BaseUserJsonUpload.headers + [
        {"property": "structure_level", "type": "string"},
        {"property": "number", "type": "string"},
        {"property": "vote_weight", "type": "decimal"},
        {"property": "comment", "type": "string"},
        {"property": "is_present", "type": "boolean"},
        {"property": "groups", "type": "string", "is_object": True, "is_list": True},
    ]
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS
    import_name = "participant"
    groups: Dict[str, int] = {}
    default_group: Dict[str, Union[int, str]] = {}

    def validate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        results = super().validate_entry(entry)
        groups = (entry := results["data"]).get("groups", [])
        messages = results["messages"]
        grp_objects: List[Dict[str, Any]] = []
        not_founds: List[str] = []
        found = False
        for group in groups:
            if id_ := self.groups.get(group):
                grp_objects.append(
                    {"value": group, "info": ImportState.DONE, "id": id_}
                )
                found = True
            else:
                grp_objects.append({"value": group, "info": ImportState.WARNING})
                not_founds.append(group)
        if not found:
            if not self.default_group.get("name") or not self.default_group.get("id"):
                raise ActionException(
                    "No valid group given in import and no default_group for meeting defined!"
                )
            grp_objects.append(
                {
                    "value": self.default_group["name"],
                    "info": ImportState.GENERATED,
                    "id": self.default_group["id"],
                }
            )
        entry["groups"] = grp_objects
        if not_founds:
            messages.append(
                f"Following groups were not found: '{', '.join(not_founds)}'"
            )
        return results

    def setup_lookups(
        self, data: List[Dict[str, Any]], meeting_id: Optional[int] = None
    ) -> None:
        super().setup_lookups(data)
        groups = self.datastore.filter(
            "group",
            FilterOperator("meeting_id", "=", meeting_id),
            mapped_fields=["name", "id", "default_group_for_meeting_id"],
        )
        for group in groups.values():
            if group["default_group_for_meeting_id"]:
                self.default_group = {"name": group["name"], "id": group["id"]}
                break
        self.groups = {group["name"]: group["id"] for group in groups.values()}
