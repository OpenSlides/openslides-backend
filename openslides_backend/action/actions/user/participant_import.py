from typing import Any, cast

from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ...mixins.import_mixins import ImportRow, ImportState
from ...util.register import register_action
from ...util.typing import ActionData
from .base_import import BaseUserImport
from .participant_common import ParticipantCommon
from .set_present import UserSetPresentAction


@register_action("participant.import")
class ParticipantImport(BaseUserImport, ParticipantCommon):
    import_name = "participant"

    def prefetch(self, action_data: ActionData) -> None:
        super().prefetch(action_data)
        self.meeting_id = cast(int, self.result["meeting_id"])

    def validate_entry(self, row: ImportRow) -> None:
        super().validate_entry(row)
        entry = row["data"]
        entry["meeting_id"] = self.meeting_id
        if "groups" not in entry:
            raise ActionException(
                f"There is no group in the data of user '{self.get_value_from_union_str_object(entry.get('username'))}'. Is there a default group for the meeting?"
            )
        groups = entry.pop("groups", None)
        entry["group_ids"] = [
            group_id for group in groups if (group_id := group.get("id"))
        ]
        failing_fields = self.permission_check.get_failing_fields(entry)
        failing_fields_jsonupload = {
            field
            for field in entry
            if isinstance(entry[field], dict)
            and entry[field]["info"] == ImportState.REMOVE
        }
        if less_ff := list(failing_fields_jsonupload - set(failing_fields)):
            less_ff.sort()
            row["messages"].append(
                f"In contrast to preview you may import field(s) '{', '.join(less_ff)}'"
            )
            for field in less_ff:
                entry[field]["info"] = ImportState.DONE
        if more_ff := list(set(failing_fields) - failing_fields_jsonupload):
            more_ff.sort()
            row["messages"].append(
                f"Error: In contrast to preview you may not import field(s) '{', '.join(more_ff)}'"
            )
            row["state"] = ImportState.ERROR
            for field in more_ff:
                entry[field]["info"] = ImportState.ERROR
        entry.pop("group_ids")
        entry["groups"] = groups

        valid = False
        for group in groups:
            if not (group_id := group.get("id")):
                continue
            if group_id in self.group_names_lookup:
                if self.group_names_lookup[group_id] == group["value"]:
                    valid = True
                else:
                    group["info"] = ImportState.WARNING
                    row["messages"].append(
                        f"Expected group '{group_id} {group['value']}' changed its name to '{self.group_names_lookup[group_id]}'."
                    )
            else:
                group["info"] = ImportState.WARNING
                row["messages"].append(
                    f"Group '{group_id} {group['value']}' doesn't exist anymore"
                )
        if not valid:
            row["messages"].append(
                "Error in groups: No valid group found inside the pre checked groups from import, see warnings."
            )
            row["state"] = ImportState.ERROR
            groups[0]["info"] = ImportState.ERROR

        entry.pop("meeting_id")
        if row["state"] == ImportState.ERROR and self.import_state == ImportState.DONE:
            self.import_state = ImportState.ERROR

    def create_other_actions(self, rows: list[ImportRow]) -> list[int | None]:
        set_present_payload: list[dict[str, Any]] = []
        indices_to_set_presence_and_id: list[tuple[bool, int | None] | None] = []
        for row in rows:
            if (present := row["data"].get("is_present")) is not None:
                indices_to_set_presence_and_id.append((present, row["data"].get("id")))
                row["data"].pop("is_present")
            else:
                indices_to_set_presence_and_id.append(None)
            row["data"]["meeting_id"] = self.meeting_id

        ids = super().create_other_actions(rows)
        for i in range(len(indices_to_set_presence_and_id)):
            if (tup := indices_to_set_presence_and_id[i]) is not None:
                present, id_ = tup
                set_present_payload.append(
                    {
                        "id": id_ or ids[i],
                        "meeting_id": self.meeting_id,
                        "present": present,
                    }
                )
        if set_present_payload:
            self.execute_other_action(UserSetPresentAction, set_present_payload)
        return ids

    def setup_lookups(self) -> None:
        super().setup_lookups()
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "group",
                    list(
                        {
                            group_id
                            for row in self.rows
                            for group in row["data"].get("groups", [])
                            if (group_id := group.get("id"))
                        }
                    ),
                    ["name"],
                )
            ],
            lock_result=False,
            use_changed_models=False,
        )
        self.group_names_lookup = {
            k: v["name"] for k, v in result.get("group", {}).items()
        }
