from typing import Any, Dict, List

from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ...mixins.import_mixins import ImportRow, ImportState
from ...util.register import register_action
from ...util.typing import ActionData
from .base_import import BaseUserImport
from .set_present import UserSetPresentAction


@register_action("participant.import")
class ParticipantImport(BaseUserImport):
    import_name = "participant"

    def prefetch(self, action_data: ActionData) -> None:
        super().prefetch(action_data)
        self.meeting_id = self.result["meeting_id"]

    def create_other_actions(self, rows: List[ImportRow]) -> None:
        set_present_payload: List[Dict[str, Any]] = []
        for row in rows:
            if (present := row["data"].get("is_present")) is not None:
                set_present_payload.append(
                    {
                        "id": row["data"]["id"],
                        "meeting_id": self.meeting_id,
                        "present": present,
                    }
                )
                row["data"].pop("is_present")
            groups = row["data"].pop("groups", [])
            row["data"]["group_ids"] = [
                id_ for group in groups if (id_ := group.get("id"))
            ]
            row["data"]["meeting_id"] = self.meeting_id

        super().create_other_actions(rows)
        if set_present_payload:
            self.execute_other_action(UserSetPresentAction, set_present_payload)

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        """ " Passthru call on base import will check self.permission, which is not determined.
        Instead use the single calls to user.create/update for permission checking"""

    def validate_entry(self, row: ImportRow) -> ImportRow:
        row = super().validate_entry(row)
        entry = row["data"]
        if "groups" not in entry:
            raise ActionException(
                f"There is no group in the data of user '{self.get_value_from_union_str_object(entry.get('username'))}'. Is there a default group for the meeting?"
            )
        valid = False
        for group in (groups := entry["groups"]):
            if not (group_id := group.get("id")):
                continue
            if group_id in self.group_names_lookup:
                if self.group_names_lookup[group_id] == group["value"]:
                    valid = True
                else:
                    group["info"] = ImportState.WARNING
                    row["messages"].append(
                        f"Expected group '{group_id} {group['value']}' changed it's name to '{self.group_names_lookup[group_id]}'."
                    )
            else:
                group["info"] = ImportState.WARNING
                row["messages"].append(
                    f"Group '{group_id} {group['value']}' don't exist anymore"
                )
        if not valid:
            row["messages"].append(
                "Error in groups: No valid group found inside the pre checked groups from import, see warnings."
            )
            row["state"] = ImportState.ERROR
            groups[0]["info"] = ImportState.ERROR

        return row

    def setup_lookups(self) -> None:
        super().setup_lookups()
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "group",
                    list(
                        set(
                            group_id
                            for row in self.rows
                            for group in row["data"].get("groups", [])
                            if (group_id := group.get("id"))
                        )
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
