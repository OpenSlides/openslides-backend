from typing import Any, Dict, List, Set

from ....models.models import Committee
from ....permissions.management_levels import OrganizationManagementLevel
from ...mixins.import_mixins import ImportState, JsonUploadMixin, Lookup, ResultType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("committee.json_upload")
class CommitteeJsonUpload(JsonUploadMixin):
    """
    Committee json_upload action. First step of import a committee.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_default_schema(
        additional_required_fields={
            "data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        **model.get_properties("name", "description"),
                        "forward_to_committees": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "organization_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "committee_managers": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "meeting_name": {"type": "string"},
                        "start_date": {"type": "integer"},
                        "end_date": {"type": "integer"},
                        "meeting_admins": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "meeting_template": {"type": "string"},
                    },
                    "required": ["name"],
                    "additionalProperties": False,
                },
                "minItems": 1,
                "uniqueItems": False,
            },
        }
    )

    headers = [
        {"property": "name", "type": "string"},
        {"property": "description", "type": "string"},
        {"property": "forward_to_committees", "type": "string[]"},
        {"property": "organization_tags", "type": "string[]"},
        {"property": "committee_managers", "type": "string[]"},
        {"property": "meeting_name", "type": "string"},
        {"property": "start_date", "type": "date"},
        {"property": "end_date", "type": "date"},
        {"property": "meeting_admins", "type": "string[]"},
        {"property": "meeting_template", "type": "string"},
    ]
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        data = instance.pop("data")
        duplicate_checker = Lookup(
            self.datastore, "committee", [entry["name"] for entry in data]
        )
        meeting_lookup = Lookup(
            self.datastore,
            "meeting",
            [
                entry.get("meeting_template")
                for entry in data
                if entry.get("meeting_template")
            ],
        )
        usernames: Set[str] = set()
        organization_tags: Set[str] = set()
        committee_names: Set[str] = set()
        for entry in data:
            if entry.get("committee_managers"):
                usernames.update(entry["committee_managers"])
            if entry.get("meeting_admins"):
                usernames.update(entry["meeting_admins"])
            if entry.get("organization_tags"):
                organization_tags.update(entry["organization_tags"])
            if entry.get("forward_to_committees"):
                committee_names.update(entry["forward_to_committees"])
        username_lookup = Lookup(
            self.datastore, "user", list(usernames), field="username"
        )
        organization_tag_lookup = Lookup(
            self.datastore, "organization_tag", list(organization_tags)
        )
        committee_lookup = Lookup(self.datastore, "committee", list(committee_names))

        self.rows = [
            self.validate_entry(
                entry,
                duplicate_checker,
                meeting_lookup,
                username_lookup,
                organization_tag_lookup,
                committee_lookup,
            )
            for entry in data
        ]

        without_template = sum(
            1
            for entry in self.rows
            if entry["data"].get("meeting_name")
            and not entry["data"].get("meeting_template")
        )
        with_template = sum(
            1
            for entry in self.rows
            if entry["data"].get("meeting_name")
            and entry["data"].get("meeting_template")
        )

        self.statistics = [
            {
                "name": "Tags created",
                "value": self.count_info("organization_tags", ImportState.NEW),
            },
            {"name": "Committees created", "value": self.count_state(ImportState.NEW)},
            {"name": "Committees updated", "value": self.count_state(ImportState.DONE)},
            {
                "name": "Additional committees have been created, because they are mentioned in the forwardings",
                "value": self.count_info("forward_to_committees", ImportState.NEW),
            },
            {"name": "Meetings created without template", "value": without_template},
            {"name": "Meetings copied from template", "value": with_template},
            {
                "name": "Committee managers relations",
                "value": self.count_len("committee_managers"),
            },
            {
                "name": "Meeting administrator relations",
                "value": self.count_len("meeting_admins"),
            },
        ]
        self.set_state(
            self.count_state(ImportState.ERROR), self.count_state(ImportState.WARNING)
        )
        self.store_rows_in_the_action_worker("committee")
        return {}

    def validate_entry(
        self,
        entry: Dict[str, Any],
        duplicate_checker: Lookup,
        meeting_lookup: Lookup,
        username_lookup: Lookup,
        organization_tag_lookup: Lookup,
        committee_lookup: Lookup,
    ) -> Dict[str, Any]:
        state, messages = None, []
        check_result = duplicate_checker.check_duplicate(entry["name"])
        if check_result == ResultType.FOUND_ID:
            state = ImportState.DONE
            entry["id"] = duplicate_checker.get_id_by_name(entry["name"])
        elif check_result == ResultType.NOT_FOUND:
            state = ImportState.NEW
        elif check_result == ResultType.FOUND_MORE_IDS:
            state = ImportState.ERROR
            messages.append("Found more committees with the same name in db.")
        else:
            state = ImportState.ERROR
            messages.append("Found more committees with the same name in csv file.")
        if any(
            field in entry
            for field in (
                "start_date",
                "end_date",
                "meeting_admins",
                "meeting_template",
            )
        ):
            if "meeting_name" not in entry:
                state = ImportState.WARNING if state != ImportState.ERROR else state
                messages.append("No meeting will be created without meeting_name")

        if (
            entry.get("start_date")
            and not entry.get("end_date")
            or not entry.get("start_date")
            and entry.get("end_date")
        ):
            state = ImportState.ERROR
            messages.append("Only one of start_date and end_date is not allowed.")
        if "meeting_template" in entry:
            result_type = meeting_lookup.check_duplicate(entry["meeting_template"])
            if result_type == ResultType.FOUND_ID:
                entry["meeting_template"] = {
                    "value": entry["meeting_template"],
                    "info": ImportState.DONE,
                    "id": meeting_lookup.get_id_by_name(entry["meeting_template"]),
                }
            else:
                entry["meeting_template"] = {
                    "value": entry["meeting_template"],
                    "info": ImportState.WARNING,
                }
        self.check_list_field("committee_managers", entry, username_lookup)
        self.check_list_field("meeting_admins", entry, username_lookup)
        self.check_list_field(
            "organization_tags",
            entry,
            organization_tag_lookup,
            not_found_state=ImportState.NEW,
        )
        self.check_list_field(
            "forward_to_committees",
            entry,
            committee_lookup,
            not_found_state=ImportState.NEW,
        )
        return {"state": state, "messages": messages, "data": entry}

    def check_list_field(
        self,
        field: str,
        entry: Dict[str, Any],
        user_lookup: Lookup,
        not_found_state: ImportState = ImportState.WARNING,
    ) -> None:
        if entry.get(field):
            new_list: List[Dict[str, Any]] = []
            for username in entry[field]:
                if user_id := user_lookup.get_id_by_name(username):
                    new_list.append(
                        {"value": username, "info": ImportState.DONE, "id": user_id}
                    )
                else:
                    new_list.append({"value": username, "info": not_found_state})
            entry[field] = new_list

    def count_info(self, field: str, state: ImportState) -> int:
        return sum(
            1
            for entry in self.rows
            for fieldentry in (entry["data"].get(field) or [])
            if fieldentry["info"] == state
        )

    def count_state(self, state: ImportState) -> int:
        return sum(1 for entry in self.rows if entry["state"] == state)

    def count_len(self, field: str) -> int:
        return sum(len(entry["data"].get(field) or []) for entry in self.rows)
