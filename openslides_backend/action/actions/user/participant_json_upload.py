from typing import Any, Dict, List, Optional, Union, cast

from openslides_backend.models.models import MeetingUser
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.filters import FilterOperator
from openslides_backend.shared.schema import required_id_schema, str_list_schema

from ...mixins.import_mixins import ImportState
from ...util.register import register_action
from ...util.typing import ActionData
from .base_json_upload import BaseUserJsonUpload
from .participant_common import ParticipantCommon


@register_action("participant.json_upload")
class ParticipantJsonUpload(BaseUserJsonUpload, ParticipantCommon):
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
    headers = [
        {"property": "title", "type": "string", "is_object": True},
        {"property": "first_name", "type": "string", "is_object": True},
        {"property": "last_name", "type": "string", "is_object": True},
        {"property": "is_active", "type": "boolean", "is_object": True},
        {"property": "is_physical_person", "type": "boolean", "is_object": True},
        {"property": "default_password", "type": "string", "is_object": True},
        {"property": "email", "type": "string", "is_object": True},
        {"property": "username", "type": "string", "is_object": True},
        {"property": "gender", "type": "string", "is_object": True},
        {"property": "pronoun", "type": "string", "is_object": True},
        {"property": "saml_id", "type": "string", "is_object": True},
        {"property": "structure_level", "type": "string", "is_object": True},
        {"property": "number", "type": "string", "is_object": True},
        {"property": "vote_weight", "type": "decimal", "is_object": True},
        {"property": "comment", "type": "string", "is_object": True},
        {"property": "is_present", "type": "boolean", "is_object": True},
        {"property": "groups", "type": "string", "is_object": True, "is_list": True},
    ]
    import_name = "participant"
    groups: Dict[str, int] = {}
    default_group: Dict[str, Union[int, str]] = {}

    def prefetch(self, action_data: ActionData) -> None:
        self.meeting_id = cast(List[Dict[str, Any]], action_data)[0].get(
            "meeting_id", 0
        )

    def validate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        entry["meeting_id"] = self.meeting_id
        results = super().validate_entry(entry)

        group_names = (entry := results["data"]).get("groups", [])
        messages = results["messages"]
        grp_objects: List[Dict[str, Any]] = []
        not_founds: List[str] = []
        found = False
        for group_name in group_names:
            if id_ := self.lookup_group_ids.get(group_name):
                grp_objects.append(
                    {"value": group_name, "info": ImportState.DONE, "id": id_}
                )
                found = True
            else:
                grp_objects.append({"value": group_name, "info": ImportState.WARNING})
                not_founds.append(group_name)
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

        groups = entry.pop("groups", None)
        entry["group_ids"] = [
            group_id for group in groups if (group_id := group.get("id"))
        ]
        payload_index = entry.pop("payload_index", None)
        failing_fields = self.permission_check.get_failing_fields(entry)
        entry.pop("group_ids")
        entry.pop("meeting_id")

        if "username" in failing_fields and not entry["username"].get("id"):
            failing_fields.remove("username")
        if failing_fields:
            messages.append(
                f"Following fields were removed from payload, because the user has no permissions to change them: {', '.join(failing_fields)}"
            )
        field_to_fail = (
            set(entry.keys()) & self.permission_check.get_all_checked_fields()
        )
        for field in field_to_fail:
            if field in failing_fields:
                if isinstance(entry[field], dict):
                    if entry[field]["info"] != ImportState.ERROR:
                        entry[field]["info"] = ImportState.REMOVE
                else:
                    entry[field] = {"value": entry[field], "info": ImportState.REMOVE}
            else:
                if not isinstance(entry[field], dict):
                    entry[field] = {"value": entry[field], "info": ImportState.DONE}

        if vote_weight := entry.get("vote_weight"):
            if (
                vote_weight["value"] == "0.000000"
                and vote_weight["info"] != ImportState.REMOVE
            ):
                entry["vote_weight"] = {
                    "value": vote_weight["value"],
                    "info": ImportState.ERROR,
                }
                messages.append("vote_weight must be bigger than or equal to 0.000001.")
                results["state"] = ImportState.ERROR

        if groups:
            entry["groups"] = groups
        if payload_index:
            entry["payload_index"] = payload_index

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
        self.lookup_group_ids = {
            group["name"]: group["id"] for group in groups.values()
        }
