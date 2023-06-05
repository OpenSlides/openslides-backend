from typing import Any, Dict, List, Set, Tuple

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
NEW_COMMITEE_ID = 0


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
        {"property": "forward_to_committees", "type": "string", "is_object": True, "is_list": True},
        {"property": "organization_tags", "type": "string", "is_object": True, "is_list": True},
        {"property": "committee_managers", "type": "string", "is_object": True, "is_list": True},
        {"property": "meeting_name", "type": "string"},
        {"property": "start_time", "type": "date"},
        {"property": "end_time", "type": "date"},
        {"property": "meeting_admins", "type": "string", "is_object": True, "is_list": True},
        {"property": "meeting_template", "type": "string",  "is_object": True},
    ]
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
    row_state: ImportState

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        data = instance.pop("data")

        # setup the lookups
        usernames: Set[str] = set()
        organization_tags: Set[str] = set()
        committee_names: Set[str] = set()
        for entry in data:
            committee_names.add(entry["name"])
            if entry.get("forward_to_committees") and not isinstance(
                entry["forward_to_committees"], str
            ):
                committee_names.update(entry["forward_to_committees"])
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

        self.committee_lookup = Lookup(
            self.datastore, "committee", list(committee_names)
        )
        self.username_lookup = Lookup(
            self.datastore, "user", list(usernames), field="username"
        )
        self.organization_tag_lookup = Lookup(
            self.datastore, "organization_tag", list(organization_tags)
        )
        self.meeting_lookup = Lookup(
            self.datastore,
            "meeting",
            list(
                set(
                    (
                        entry.get("meeting_template")
                        for entry in data
                        if entry.get("meeting_template")
                    )
                )
            ),
        )
        # found_committee = [
        #     entry["name"]
        #     for entry in data
        #     if committee_lookup.check_duplicate(entry["name"]) == ResultType.NOT_FOUND
        # ]
        # special case: we want to find committees, which are new created
        # for the forwarding. Handled in check_list_field().
        # for name in found_committee:
        #    committee_lookup.name_to_ids[name].append(NEW_COMMITEE_ID)

        # main work, see validate_entry
        self.rows = [self.validate_entry(entry) for entry in data]

        # calculate statistics
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
                "value": len([v for v in self.organization_tag_lookup.name_to_ids.values() if not v]),
            },
        ]

        # set state and store in action worker
        self.set_state(
            self.count_state(ImportState.ERROR), self.count_state(ImportState.WARNING)
        )
        self.store_rows_in_the_action_worker("committee")
        return {}

    def validate_entry(
        self,
        entry: Dict[str, Any],
    ) -> Dict[str, Any]:
        messages: List[str] = []

        # committee state handling
        check_result = self.committee_lookup.check_duplicate(entry["name"])
        if check_result == ResultType.FOUND_ID:
            self.row_state = ImportState.DONE
            entry["id"] = self.committee_lookup.get_id_by_name(entry["name"])
        elif check_result == ResultType.NOT_FOUND:
            self.row_state = ImportState.NEW
        elif check_result == ResultType.FOUND_MORE_IDS:
            self.row_state = ImportState.ERROR
            messages.append("Found more committees with the same name in db.")

        if not entry.get("meeting_name"):
            if any(
                entry.get(field)
                for field in (
                    "start_time",
                    "end_time",
                    "meeting_admins",
                    "meeting_template",
                )
            ):
                messages.append("No meeting will be created without meeting_name")
        else:
            entry, check_messages = self.meeting_checks(entry)
            messages.extend(check_messages)

        # handle committee managers (string list)
        self.check_list_field(
            "committee_managers", entry, self.username_lookup, messages
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

        # handle organization tags
        self.check_list_field(
            "organization_tags",
            entry,
            self.organization_tag_lookup,
            messages,
            not_found_state=ImportState.NEW,
        )

        # handle forward_to_committees
        self.check_list_field(
            "forward_to_committees",
            entry,
            self.committee_lookup,
            messages,
            not_found_state=ImportState.NEW,
        )
        return {"state": self.row_state, "messages": messages, "data": entry}

    def check_list_field(
        self,
        field: str,
        entry: Dict[str, Any],
        lookup: Lookup,
        messages: List[str],
        not_found_state: ImportState = ImportState.WARNING,
    ) -> None:
        # TODO überarbeiten das ganze, not_found_state, remove etc.
        if field in entry:
            # check for parse error
            if isinstance(entry[field], str):
                messages.append(f"Could not parse {entry[field]}: expected string[]")
                self.row_state = ImportState.ERROR
                return

            # new_list is the new list of object
            new_list: List[Dict[str, Any]] = []
            # found_list and remove_list are used to cut duplicates
            found_list: List[str] = []
            remove_list: List[str] = []
            for name in entry[field]:
                check_duplicate = lookup.check_duplicate(name)
                if name in found_list:
                    remove_list.append(name)
                elif check_duplicate == ResultType.FOUND_ID:
                    id_ = lookup.get_id_by_name(name)
                    if id_:
                        new_list.append(
                            {"value": name, "info": ImportState.DONE, "id": id_}
                        )
                    else:
                        new_list.append({"value": name, "info": not_found_state})

                else:
                    new_list.append({"value": name, "info": not_found_state})
                found_list.append(name)
            entry[field] = new_list

            if remove_list:
                remove_list_str = ", ".join(remove_list)
                messages.append(
                    f"Removed duplicated {field.replace('_', ' ')}: [{remove_list_str}]"
                )

    def date_checks(self, entry: Dict[str, Any]) -> List[str]:
        messages: List[str] = []
        parse_error = False
        if (starttime := entry.get("start_time")) and not isinstance(starttime, int):
            parse_error = True
            self.row_state = ImportState.ERROR
            messages.append(f"Could not parse start_time {starttime}: expected date")
        if (endtime := entry.get("end_time")) and not isinstance(endtime, int):
            parse_error = True
            self.row_state = ImportState.ERROR
            messages.append(f"Could not parse end_time {starttime}: expected date")
        if not parse_error:
            if bool(starttime) ^ bool(endtime):
                self.row_state = ImportState.ERROR
                messages.append("Only one of start_time and end_time is not allowed.")
            elif isinstance(starttime, int) and starttime > endtime:
                self.row_state = ImportState.ERROR
                messages.append("Start time may not be after end time.")
        return messages

    def meeting_checks(self, entry: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        messages: List[str] = []

        check_messages = self.date_checks(entry)
        messages.extend(check_messages)

        if not (meeting_template := entry.get("meeting_template")):
            entry["meeting_template"] = {
                "value": meeting_template,
                "info": ImportState.NONE,
            }
        else:
            result_type = self.meeting_lookup.check_duplicate(meeting_template)
            if result_type == ResultType.FOUND_ID:
                entry["meeting_template"] = {
                    "value": meeting_template,
                    "info": ImportState.DONE,
                    "id": self.meeting_lookup.get_id_by_name(meeting_template),
                }
            else:
                entry["meeting_template"] = {
                    "value": "meeting_template",
                    "info": ImportState.WARNING,
                }
                messages.append("Meeting will be created with meeting.create.")

        # handle meeting_admins
        self.check_list_field("meeting_admins", entry, self.username_lookup, messages)
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

        return entry, messages

    def count_state(self, state: ImportState) -> int:
        return sum(1 for entry in self.rows if entry["state"] == state)
