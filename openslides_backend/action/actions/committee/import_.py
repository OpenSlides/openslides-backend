from typing import Any

from openslides_backend.action.actions.meeting.clone import MeetingClone
from openslides_backend.action.actions.meeting.create import MeetingCreate
from openslides_backend.action.actions.organization_tag.create import (
    OrganizationTagCreate,
)
from openslides_backend.action.util.typing import ActionData, ActionResults
from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID

from ....permissions.management_levels import OrganizationManagementLevel
from ...mixins.import_mixins import BaseImportAction, ImportRow, ImportState, Lookup
from ...util.register import register_action
from .create import CommitteeCreate
from .import_mixin import CommitteeImportMixin
from .update import CommitteeUpdateAction

DEFAULT_TAG_COLOR = "#2196f3"


@register_action("committee.import")
class CommitteeImport(BaseImportAction, CommitteeImportMixin):
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
    import_name = "committee"

    field_map = {
        **{
            field: field[:-1] + "_ids"
            for field in (
                "forward_to_committees",
                "managers",
                "meeting_admins",
                "organization_tags",
            )
        },
        "parent": "parent_id",
    }

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        super().update_instance(instance)
        self.setup_lookups()
        for row in self.rows:
            self.validate_entry(row)
        if self.check_parents_for_circles(self.rows):
            self.import_state = ImportState.ERROR

        if self.import_state != ImportState.ERROR:
            rows = self.flatten_copied_object_fields(self.handle_relation_fields)
            self.create_models(rows)

        return {}

    def validate_entry(self, row: ImportRow) -> None:
        self.validate_with_lookup(row, self.committee_lookup)
        self.validate_field(row, self.meeting_map, "meeting_template", False)
        self.validate_field(row, self.committee_map, "parent", False)
        self.validate_field(row, self.committee_map, "forward_to_committees")
        self.validate_field(row, self.user_map, "managers")
        self.validate_field(row, self.user_map, "meeting_admins")
        self.check_admin_groups_for_meeting(row)
        if row["state"] == ImportState.ERROR:
            self.import_state = ImportState.ERROR
        self.validate_field(row, self.organization_tag_map, "organization_tags")

    def handle_relation_fields(self, entry: dict[str, Any]) -> dict[str, Any]:
        # filter out invalid entries & replace valid ones with ids
        for field in ("managers", "meeting_admins"):
            if field in entry:
                entry[field] = [
                    id
                    for user in entry[field]
                    if (id := user.get("id")) and user["info"] == ImportState.DONE
                ]
        # only filter out invalid entries, the id replacement is done later
        for field in ("organization_tags", "forward_to_committees"):
            if field in entry:
                entry[field] = [
                    obj
                    for obj in entry[field]
                    if obj["info"] in (ImportState.DONE, ImportState.NEW)
                ]
        if template := entry.get("meeting_template"):
            if template["info"] != ImportState.DONE:
                entry.pop("meeting_template")
            else:
                entry["meeting_template"] = template["id"]
        if parent := entry.get("parent"):
            if parent["value"] in ["", None]:
                entry.pop("parent")
            else:
                entry["parent"] = parent["value"]
                if parent_id := parent.get("id"):
                    entry["parent_id"] = parent_id
                    entry.pop("parent")
        return entry

    def create_models(self, rows: list[ImportRow]) -> None:
        # create tags & update row data
        create_tag_data: list[dict[str, Any]] = []
        for row in rows:
            for tag in row["data"].get("organization_tags", []):
                if isinstance(tag, str):
                    create_tag_data.append(
                        {
                            "name": tag,
                            "color": DEFAULT_TAG_COLOR,
                            "organization_id": ONE_ORGANIZATION_ID,
                        }
                    )
        if create_tag_data:
            results = self.execute_other_action(OrganizationTagCreate, create_tag_data)
            self.update_rows_from_results(
                rows, create_tag_data, results, "organization_tags"
            )

        # create missing committees & update row data
        create_committee_data: list[dict[str, Any]] = []
        for row in rows:
            entry = row["data"]
            if "id" not in entry:
                create_committee_data.append(
                    {"name": entry["name"], "organization_id": ONE_ORGANIZATION_ID}
                )
        if create_committee_data:
            results = self.execute_other_action(CommitteeCreate, create_committee_data)
            self.update_rows_from_results(
                rows,
                create_committee_data,
                results,
                "forward_to_committees",
                True,
            )
            self.update_rows_from_results(
                rows,
                create_committee_data,
                results,
                "parent",
                True,
            )

        # rename relation fields
        for row in rows:
            entry = row["data"]
            for old, new in self.field_map.items():
                if old in entry:
                    entry[new] = entry.pop(old)

        # execute committee updates
        update_committee_data: list[dict[str, Any]] = []
        for row in rows:
            entry = row["data"]
            action_data = {
                field: entry[field]
                for field in (
                    "id",
                    "description",
                    "forward_to_committee_ids",
                    "manager_ids",
                    "organization_tag_ids",
                    "parent_id",
                )
                if field in entry
            }
            update_committee_data.append(action_data)
        if update_committee_data:
            self.execute_other_action(CommitteeUpdateAction, update_committee_data)

        # create meetings
        lang = self.get_organization_language()
        create_meeting_data: list[dict[str, Any]] = []
        clone_meeting_data: list[dict[str, Any]] = []
        for row in rows:
            entry = row["data"]
            if "meeting_name" in entry:
                action_data = {
                    field: entry[meeting_field]
                    for field in (
                        "name",
                        "start_time",
                        "end_time",
                        "admin_ids",
                    )
                    if (meeting_field := f"meeting_{field}") in entry
                } | {
                    "committee_id": entry["id"],
                }
                if template_id := entry.get("meeting_template"):
                    action_data["meeting_id"] = template_id
                    clone_meeting_data.append(action_data)
                else:
                    action_data["language"] = lang
                    create_meeting_data.append(action_data)
        if create_meeting_data:
            self.execute_other_action(MeetingCreate, create_meeting_data)
        if clone_meeting_data:
            self.execute_other_action(MeetingClone, clone_meeting_data)

    def update_rows_from_results(
        self,
        rows: list[ImportRow],
        action_data: ActionData,
        results: ActionResults | None,
        field: str,
        update_ids: bool = False,
    ) -> None:
        name_map = {
            action_data["name"]: result["id"]
            for action_data, result in zip(action_data, results or [])
            if result
        }
        for row in rows:
            entry = row["data"]
            if update_ids and "id" not in entry:
                entry["id"] = name_map[entry["name"]]
            if val := entry.pop(field, None):  # pop field to rename it
                # replace names with ids
                if isinstance(val, list):
                    for i in range(len(val)):
                        if isinstance(val[i], str):
                            if val[i] not in name_map:
                                val[i] = None
                            else:
                                val[i] = name_map[val[i]]
                    entry[self.field_map.get(field, field)] = list(filter(None, val))
                else:
                    if isinstance(val, str):
                        if val not in name_map:
                            val = None
                        else:
                            val = name_map[val]
                    entry[self.field_map.get(field, field)] = val

    def get_organization_language(self) -> str:
        organization = self.datastore.get(
            ONE_ORGANIZATION_FQID,
            ["default_language"],
            lock_result=False,
            use_changed_models=False,
        )
        return organization["default_language"]

    def setup_lookups(self) -> None:
        self.committee_lookup = Lookup(
            self.datastore,
            "committee",
            [
                (entry["name"]["value"], entry)
                for row in self.rows
                if (entry := row["data"])
            ],
        )
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "committee",
                    [
                        id
                        for row in self.rows
                        for committee in [
                            row["data"].get("parent", {}),
                            *row["data"].get("forward_to_committees", []),
                        ]
                        if (id := committee.get("id"))
                    ],
                    ["name"],
                ),
                GetManyRequest(
                    "user",
                    [
                        id
                        for row in self.rows
                        for user in row["data"].get("managers", [])
                        + row["data"].get("meeting_admins", [])
                        if (id := user.get("id"))
                    ],
                    ["username"],
                ),
                GetManyRequest(
                    "organization_tag",
                    [
                        id
                        for row in self.rows
                        for tag in row["data"].get("organization_tags", [])
                        if (id := tag.get("id"))
                    ],
                    ["name"],
                ),
                GetManyRequest(
                    "meeting",
                    [
                        id
                        for row in self.rows
                        if (id := row["data"].get("meeting_template", {}).get("id"))
                    ],
                    ["name"],
                ),
            ],
            lock_result=False,
            use_changed_models=False,
        )
        self.committee_map = {
            k: v["name"] for k, v in result.get("committee", {}).items()
        }
        self.user_map = {k: v["username"] for k, v in result.get("user", {}).items()}
        self.organization_tag_map = {
            k: v["name"] for k, v in result.get("organization_tag", {}).items()
        }
        self.meeting_map = {k: v["name"] for k, v in result.get("meeting", {}).items()}
