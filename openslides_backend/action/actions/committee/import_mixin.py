from typing import Any

from openslides_backend.shared.filters import FilterOperator

from ...action import Action
from ...mixins.import_mixins import ImportRow, ImportState


class CommitteeImportMixin(Action):
    def check_admin_groups_for_meeting(self, row: dict[str, Any] | ImportRow) -> None:
        entry = row["data"]
        if entry.get("meeting_name") and not any(
            admin
            for admin in entry.get("meeting_admins", [])
            if admin.get("info") == ImportState.DONE
        ):
            admin_ids: list[int] = []
            if (
                template_id := entry.get("meeting_template", {}).get("id")
            ) and entry.get("meeting_template", {}).get("info") == ImportState.DONE:
                groups = self.datastore.filter(
                    "group",
                    FilterOperator("admin_group_for_meeting_id", "=", template_id),
                    ["meeting_user_ids"],
                )
                admin_ids = [
                    meeting_user_id
                    for group in groups.values()
                    for meeting_user_id in (group.get("meeting_user_ids") or [])
                ]
            if not len(admin_ids):
                row["state"] = ImportState.ERROR
                entry["meeting_admins"] = [
                    *entry.get("meeting_admins", []),
                    {"value": "", "info": ImportState.ERROR},
                ]
                row["messages"].append(
                    "Error: Meeting cannot be created without admins"
                )
