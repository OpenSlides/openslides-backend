from collections.abc import Iterable
from typing import Any

from openslides_backend.models.models import MeetingUser
from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.patterns import fqid_from_collection_and_id
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
                "number",
                "vote_weight",
                "comment",
            ),
            "is_present": {"type": "boolean"},
            "structure_level": str_list_schema,
            "groups": str_list_schema,
        },
    )
    headers = [
        header | {"is_object": True} for header in BaseUserJsonUpload.headers
    ] + [
        {
            "property": "structure_level",
            "type": "string",
            "is_object": True,
            "is_list": True,
        },
        {"property": "number", "type": "string", "is_object": True},
        {"property": "vote_weight", "type": "decimal", "is_object": True},
        {"property": "comment", "type": "string", "is_object": True},
        {"property": "is_present", "type": "boolean", "is_object": True},
        {"property": "groups", "type": "string", "is_object": True, "is_list": True},
    ]
    import_name = "participant"
    lookups: dict[str, dict[str, int]] = {}
    default_group: dict[str, Any] = {}
    missing_field_values: dict[str, set[str]]

    def prefetch(self, action_data: ActionData) -> None:
        self.meeting_id = next(iter(action_data)).get("meeting_id", 0)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        self.missing_field_values = {}
        data = super().update_instance(instance)
        self.statistics.extend(
            [
                {
                    "name": "structure levels created",
                    "value": len(self.missing_field_values.get("structure_level", [])),
                },
                {
                    "name": "groups created",
                    "value": len(self.missing_field_values.get("groups", [])),
                },
            ]
        )
        return data

    def validate_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        entry["meeting_id"] = self.meeting_id
        results = super().validate_entry(entry)
        messages = results["messages"]
        entry = results["data"]

        # validate groups
        found, group_objects = self.validate_with_lookup(
            entry, "groups", messages, True
        )
        if not found:
            if not self.default_group.get("name") or not self.default_group.get("id"):
                raise ActionException(
                    "No valid group given in import and no default_group for meeting defined!"
                )
            group_objects.append(
                {
                    "value": self.default_group["name"],
                    "info": ImportState.GENERATED,
                    "id": self.default_group["id"],
                }
            )

        # validate structure level
        _, structure_level_objects = self.validate_with_lookup(
            entry, "structure_level", messages, True
        )

        payload_index = entry.pop("payload_index", None)
        perm_check = (
            self.permission_check_update
            if entry.get("id")
            else self.permission_check_create
        )
        failing_fields = perm_check.get_failing_fields(entry)
        entry.pop("group_ids")
        entry.pop("structure_level_ids")
        entry.pop("meeting_id")

        if "username" in failing_fields and not entry["username"].get("id"):
            failing_fields.remove("username")
        if failing_fields:
            messages.append(
                f"Following fields were removed from payload, because the user has no permissions to change them: {', '.join(failing_fields)}"
            )
        field_to_fail = set(entry.keys()) & perm_check.get_all_checked_fields()
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

        if group_objects:
            entry["groups"] = group_objects
        if structure_level_objects:
            entry["structure_level"] = structure_level_objects
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

        if payload_index:
            entry["payload_index"] = payload_index

        return results

    def validate_with_lookup(
        self,
        entry: dict[str, Any],
        field: str,
        messages: list[str],
        create_when_not_found: bool = False,
    ) -> tuple[bool, list[dict[str, Any]]]:
        singular_field = field.rstrip("s")
        names = entry.pop(field, [])
        objects: list[dict[str, Any]] = []
        missing: list[str] = []
        found = False
        for name in names:
            if id_ := self.lookups[singular_field].get(name):
                objects.append({"value": name, "info": ImportState.DONE, "id": id_})
                found = True
            elif create_when_not_found:
                objects.append({"value": name, "info": ImportState.NEW})
                missing.append(name)
                if self.missing_field_values.get(field) is None:
                    self.missing_field_values[field] = {name}
                else:
                    self.missing_field_values[field].add(name)
                found = True
            else:
                objects.append({"value": name, "info": ImportState.WARNING})
                missing.append(name)
        if missing and not create_when_not_found:
            plural_field = singular_field.replace("_", " ") + "s"
            messages.append(
                f"Following {plural_field} were not found: '{', '.join(missing)}'"
            )
        entry[f"{singular_field}_ids"] = [
            group_id for group in objects if (group_id := group.get("id"))
        ]
        return (found, objects)

    def create_lookup(self, instances: Iterable[dict[str, Any]]) -> dict[str, int]:
        return {instance["name"]: instance["id"] for instance in instances}

    def setup_lookups(self, data: list[dict[str, Any]]) -> None:
        super().setup_lookups(data)
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", self.meeting_id),
            ["group_ids", "structure_level_ids"],
        )
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "group",
                    meeting.get("group_ids", []),
                    ["name", "id", "default_group_for_meeting_id"],
                ),
                GetManyRequest(
                    "structure_level",
                    meeting.get("structure_level_ids", []),
                    ["name", "id"],
                ),
            ]
        )
        for collection in ("group", "structure_level"):
            self.lookups[collection] = self.create_lookup(result[collection].values())
        for group in result["group"].values():
            if group.get("default_group_for_meeting_id"):
                self.default_group = {"name": group["name"], "id": group["id"]}
                break
