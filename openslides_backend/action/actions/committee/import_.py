from collections import defaultdict
from typing import Any, Dict, List

from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.shared.exceptions import ActionException

from ....permissions.management_levels import OrganizationManagementLevel
from ...mixins.import_mixins import ImportMixin, ImportRow, ImportState, Lookup
from ...util.register import register_action
from .create import CommitteeCreate
from .update import CommitteeUpdateAction


@register_action("committee.import")
class CommitteeImport(ImportMixin):
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
    import_name = "committee"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        if not instance["import"]:
            return {}

        self.setup_lookups()
        for row in self.rows:
            self.validate_entry(row)

        if self.import_state != ImportState.ERROR:
            rows = self.flatten_copied_object_fields()
            self.create_committees(rows)

        return {}

    def validate_entry(self, row: ImportRow) -> None:
        self.validate_with_lookup(row, self.committee_lookup)
        self.validate_with_lookup(row, self.committee_lookup, "meeting_template", False)
        self.validate_list_field(row, self.committee_map, "forward_to_committees")
        self.validate_list_field(row, self.user_map, "committee_managers")
        self.validate_list_field(row, self.user_map, "meeting_admins")
        self.validate_list_field(row, self.organization_tag_map, "organization_tags")

    def create_committees(self, rows: List[ImportRow]) -> None:
        create_action_data: List[Dict[str, Any]] = []
        update_action_data_map: Dict[int, Dict[str, Any]] = defaultdict(dict)
        for row in rows:
            entry = row["data"]
            action_data = {
                field: entry[field]
                for field in (
                    "id",
                    "name",
                    "description",
                    "organization_tags",
                    "committee_managers",
                )
                if field in entry
            }
            if "organization_tags" in action_data:
                action_data["organization_tag_ids"] = action_data.pop(
                    "organization_tags"
                )
            if "committee_managers" in action_data:
                action_data["manager_ids"] = action_data.pop("committee_managers")
            if id := entry.get("id"):
                update_action_data_map[id] = action_data
            else:
                create_action_data.append(action_data)
        results = self.execute_other_action(CommitteeCreate, create_action_data) or []
        committee_map = {
            entry["name"]: result["id"]
            for entry, result in zip(create_action_data, results)
            if result
        }
        for row in rows:
            entry = row["data"]
            if "id" not in entry:
                entry["id"] = committee_map[entry["name"]]
            if forwards := entry.get("forward_to_committees"):
                for i in range(len(forwards)):
                    if isinstance(forwards[i], str):
                        if forwards[i] not in committee_map:
                            raise ActionException(
                                f"Unknown name in forward_to_committees: {forwards[i]}"
                            )
                        forwards[i] = committee_map[forwards[i]]
            update_action_data_map[entry["id"]]["forward_to_committee_ids"] = forwards
        self.execute_other_action(
            CommitteeUpdateAction,
            [
                {"id": id, **action_data}
                for id, action_data in update_action_data_map.items()
            ],
        )

    def setup_lookups(self) -> None:
        self.committee_lookup = Lookup(
            self.datastore,
            "committee",
            [
                (entry["name"]["value"], entry)
                for row in self.rows
                if (entry := row["data"])
            ],
            field="name",
        )
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "committee",
                    [
                        id
                        for row in self.rows
                        for committee in row["data"].get("forward_to_committees", [])
                        if (id := committee.get("id"))
                    ],
                    ["name"],
                ),
                GetManyRequest(
                    "user",
                    [
                        id
                        for row in self.rows
                        for user in row["data"].get("committee_managers", [])
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
                        for tag in row["data"].get("organisation_tags", [])
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
