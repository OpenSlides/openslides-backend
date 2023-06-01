from typing import Any, Dict, List, Optional, Set

from ....models.models import Committee
from ....permissions.management_levels import OrganizationManagementLevel
from ...mixins.import_mixins import ImportState, JsonUploadMixin, Lookup, ResultType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action

LIST_TYPE = {
    "anyOf": [
        {
            "type": "array",
            "items": {"type": "string"},
        },
        {"type": "string"},
    ]
}


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
                        "forward_to_committees": LIST_TYPE,
                        "organization_tags": LIST_TYPE,
                        "committee_managers": LIST_TYPE,
                        "meeting_name": {"type": "string"},
                        "start_time": {"type": ["integer", "string"]},
                        "end_time": {"type": ["integer", "string"]},
                        "meeting_admins": LIST_TYPE,
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
        {"property": "forward_to_committees", "type": "string", "is_list": True},
        {"property": "organization_tags", "type": "string", "is_list": True},
        {"property": "committee_managers", "type": "string", "is_list": True},
        {"property": "meeting_name", "type": "string"},
        {"property": "start_time", "type": "date"},
        {"property": "end_time", "type": "date"},
        {"property": "meeting_admins", "type": "string", "is_list": True},
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
            if entry.get("committee_managers") and not isinstance(
                entry["committee_managers"], str
            ):
                usernames.update(entry["committee_managers"])
            if entry.get("meeting_admins") and not isinstance(
                entry["meeting_admins"], str
            ):
                usernames.update(entry["meeting_admins"])
            if entry.get("organization_tags") and not isinstance(
                entry["organization_tags"], str
            ):
                organization_tags.update(entry["organization_tags"])
            if entry.get("forward_to_committees") and not isinstance(
                entry["forward_to_committees"], str
            ):
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
            and (
                not entry["data"].get("meeting_template")
                or entry["data"]["meeting_template"]["info"] != ImportState.DONE
            )
        )
        with_template = sum(
            1
            for entry in self.rows
            if entry["data"].get("meeting_name")
            and entry["data"].get("meeting_template")
            and entry["data"]["meeting_template"]["info"] == ImportState.DONE
        )

        self.statistics = [
            {
                "name": "Committees created",
                "value": self.count_state(ImportState.NEW)
                + self.count_state(ImportState.WARNING),
            },
            {"name": "Committees updated", "value": self.count_state(ImportState.DONE)},
            {"name": "Meetings created without template", "value": without_template},
            {"name": "Meetings copied from template", "value": with_template},
            {
                "name": "Organization tags created",
                "value": self.count_info("organization_tags", ImportState.NEW),
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

        if any(
            field in entry
            for field in (
                "start_time",
                "end_time",
                "meeting_admins",
                "meeting_template",
            )
        ):
            if "meeting_name" not in entry:
                state = ImportState.WARNING if state != ImportState.ERROR else state
                messages.append("No meeting will be created without meeting_name")

        if entry.get("start_time") and isinstance(entry.get("start_time"), str):
            state = ImportState.ERROR
            messages.append(f"Could not parse {entry['start_time']}: expected date")
        if entry.get("end_time") and isinstance(entry.get("end_time"), str):
            state = ImportState.ERROR
            messages.append(f"Could not parse {entry['end_time']}: expected date")

        if (
            entry.get("start_time")
            and not entry.get("end_time")
            or not entry.get("start_time")
            and entry.get("end_time")
        ):
            if state != ImportState.ERROR:
                state = ImportState.ERROR
                messages.append("Only one of start_time and end_time is not allowed.")

        if "meeting_template" in entry:
            result_type = meeting_lookup.check_duplicate(entry["meeting_template"])
            if result_type == ResultType.FOUND_ID:
                entry["meeting_template"] = {
                    "value": entry["meeting_template"],
                    "info": ImportState.DONE,
                    "id": meeting_lookup.get_id_by_name(entry["meeting_template"]),
                }
            elif entry["meeting_template"] == "":
                entry["meeting_template"] = {
                    "value": entry["meeting_template"],
                    "info": ImportState.NONE,
                }
            else:
                entry["meeting_template"] = {
                    "value": entry["meeting_template"],
                    "info": ImportState.WARNING,
                }
        if "meeting_name" in entry and (
            "meeting_template" not in entry
            or entry["meeting_template"]["info"] == ImportState.WARNING
        ):
            messages.append("Meeting will be created with meeting.create.")
        state = self.check_list_field(
            "committee_managers", entry, username_lookup, state, messages
        )
        if any(
            inner["info"] == ImportState.WARNING
            for inner in (entry.get("committee_managers") or [])
        ):
            missing_managers = ", ".join(
                [
                    inner["value"]
                    for inner in entry["committee_managers"]
                    if inner["info"] == ImportState.WARNING
                ]
            )
            messages.append(f"Missing committee manager(s): [{missing_managers}]")
        state = self.check_list_field(
            "meeting_admins", entry, username_lookup, state, messages
        )
        if any(
            inner["info"] == ImportState.WARNING
            for inner in (entry.get("meeting_admins") or [])
        ):
            missing_admins = ", ".join(
                [
                    inner["value"]
                    for inner in entry["meeting_admins"]
                    if inner["info"] == ImportState.WARNING
                ]
            )
            messages.append(f"Missing meeting admin(s): [{missing_admins}]")
        state = self.check_list_field(
            "organization_tags",
            entry,
            organization_tag_lookup,
            state,
            messages,
            not_found_state=ImportState.NEW,
        )
        state = self.check_list_field(
            "forward_to_committees",
            entry,
            committee_lookup,
            state,
            messages,
            not_found_state=ImportState.NEW,
        )
        return {"state": state, "messages": messages, "data": entry}

    def check_list_field(
        self,
        field: str,
        entry: Dict[str, Any],
        user_lookup: Lookup,
        state: Optional[ImportState],
        messages: List[str],
        not_found_state: ImportState = ImportState.WARNING,
    ) -> Optional[ImportState]:
        if field in entry:
            if isinstance(entry[field], str):
                messages.append(f"Could not parse {entry[field]}: expected string[]")
                return ImportState.ERROR
            new_list: List[Dict[str, Any]] = []
            found_list: List[str] = []
            remove_list: List[str] = []
            for username in entry[field]:
                check_duplicate = user_lookup.check_duplicate(username)
                if username in found_list:
                    remove_list.append(username)
                elif check_duplicate == ResultType.FOUND_ID:
                    user_id = user_lookup.get_id_by_name(username)
                    new_list.append(
                        {"value": username, "info": ImportState.DONE, "id": user_id}
                    )
                else:
                    new_list.append({"value": username, "info": not_found_state})
                found_list.append(username)
            entry[field] = new_list
            if remove_list:
                remove_list_str = ", ".join(remove_list)
                messages.append(
                    f"Removed duplicated {field.replace('_', ' ')}: [{remove_list_str}]"
                )
        return state

    def count_info(self, field: str, state: ImportState) -> int:
        return sum(
            1
            for entry in self.rows
            for fieldentry in (entry["data"].get(field) or [])
            if fieldentry["info"] == state
        )

    def count_state(self, state: ImportState) -> int:
        return sum(1 for entry in self.rows if entry["state"] == state)
