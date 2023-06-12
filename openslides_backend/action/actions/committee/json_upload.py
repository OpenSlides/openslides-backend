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
        {
            "property": "forward_to_committees",
            "type": "string",
            "is_object": True,
            "is_list": True,
        },
        {
            "property": "organization_tags",
            "type": "string",
            "is_object": True,
            "is_list": True,
        },
        {
            "property": "committee_managers",
            "type": "string",
            "is_object": True,
            "is_list": True,
        },
        {"property": "meeting_name", "type": "string"},
        {"property": "start_time", "type": "date"},
        {"property": "end_time", "type": "date"},
        {
            "property": "meeting_admins",
            "type": "string",
            "is_object": True,
            "is_list": True,
        },
        {"property": "meeting_template", "type": "string", "is_object": True},
    ]
    payload_db_field = {
        "forward_to_committees": "forward_to_committee_ids",
        "organization_tags": "organization_tag_ids",
        "committee_managers": "manager_ids",
    }

    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
    row_state: ImportState

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        data = instance.pop("data")
        self.setup_lookups(data)
        self.fill_committees_to_add_with_pseudo_id(data)
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
                "value": len(
                    [
                        v
                        for v in self.organization_tag_lookup.name_to_ids.values()
                        if not v
                    ]
                ),
            },
        ]

        # set state and store in action worker
        self.set_state(
            self.count_state(ImportState.ERROR), self.count_state(ImportState.WARNING)
        )
        self.store_rows_in_the_action_worker("committee")
        return {}  # do not create any write_requests, this is just for preview

    def validate_entry(
        self,
        entry: Dict[str, Any],
    ) -> Dict[str, Any]:
        messages: List[str] = []

        # committee state handling
        self.committee_name = entry["name"]
        check_result = self.committee_lookup.check_duplicate(self.committee_name)
        id_ = self.committee_lookup.get_id_by_name(self.committee_name)
        if check_result == ResultType.FOUND_ID and id_ != 0:
            self.row_state = ImportState.DONE
            entry["name"] = {
                "value": self.committee_name,
                "info": ImportState.DONE,
                "id": id_,
            }
        elif check_result == ResultType.NOT_FOUND or id_ == 0:
            self.row_state = ImportState.NEW
            entry["name"] = {"value": self.committee_name, "info": ImportState.NEW}
        elif check_result == ResultType.FOUND_MORE_IDS:
            self.row_state = ImportState.ERROR
            entry["name"] = {"value": self.committee_name, "info": ImportState.ERROR}
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

        self.check_list_field(
            "committee_managers",
            entry,
            self.username_lookup,
            messages,
            ImportState.WARNING,
        )

        self.check_list_field(
            "organization_tags",
            entry,
            self.organization_tag_lookup,
            messages,
            not_found_state=ImportState.NEW,
        )

        self.check_list_field(
            "forward_to_committees",
            entry,
            self.committee_lookup,
            messages,
            not_found_state=ImportState.WARNING,
        )
        return {"state": self.row_state, "messages": messages, "data": entry}

    def check_list_field(
        self,
        field: str,
        entry: Dict[str, Any],
        lookup: Lookup,
        messages: List[str],
        not_found_state: ImportState = ImportState.ERROR,
    ) -> None:
        if field in entry:
            # check for parse error
            if isinstance(entry[field], str):
                entry[field] = [entry[field]]

            # found_list and remove_duplicate_list are used to cut duplicates
            found_for_duplicate_list: List[str] = []
            remove_duplicate_list: List[str] = []
            remove_list: List[str] = []
            not_unique_list: List[str] = []
            missing_list: List[str] = []
            db_set_names: Set[str] = set()

            # removed objects
            if db_field := self.payload_db_field.get(field):
                db_list_ids = (
                    self.committee_lookup.name_to_ids[self.committee_name][0].get(
                        db_field, []
                    )
                    or []
                )
                db_set_names = set([lookup.id_to_name[id_] for id_ in db_list_ids])
                new_list_names = set(entry[field])
                remove_list = list(db_set_names - new_list_names)
                remove_list.sort()  # necessary for test

            for i, name in enumerate(entry[field]):
                if name in found_for_duplicate_list:
                    remove_duplicate_list.append(name)
                    entry[field][i] = {"value": name, "info": ImportState.WARNING}
                    continue

                found_for_duplicate_list.append(name)
                check_duplicate = lookup.check_duplicate(name)
                if check_duplicate == ResultType.FOUND_ID:
                    id_ = lookup.get_id_by_name(name)
                    entry[field][i] = {
                        "value": name,
                        # import states signalize a new relation, not the creation of an element
                        "info": ImportState.DONE
                        if name in db_set_names
                        else ImportState.NEW,
                    }
                    if id_:
                        entry[field][i]["id"] = id_
                elif check_duplicate == ResultType.FOUND_MORE_IDS:
                    entry[field][i] = {"value": name, "info": ImportState.WARNING}
                    not_unique_list.append(name)
                else:
                    entry[field][i] = {"value": name, "info": not_found_state}
                    if not_found_state != ImportState.NEW:
                        missing_list.append(name)

            self.append_message_for_list_fields(
                not_unique_list,
                "Not identifiable {field}, because name not unique: [{incorrects}]",
                field,
                messages,
            )
            self.append_message_for_list_fields(
                missing_list, "Missing {field}: [{incorrects}]", field, messages
            )
            self.append_message_for_list_fields(
                remove_list, "Removed {field}: [{incorrects}]", field, messages
            )
            self.append_message_for_list_fields(
                remove_duplicate_list,
                "Removed duplicated {field}: [{incorrects}]",
                field,
                messages,
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
            messages.append(f"Could not parse end_time {endtime}: expected date")
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
                    "value": meeting_template,
                    "info": ImportState.WARNING,
                }
                messages.append("Meeting will be created with meeting.create.")

        self.check_list_field(
            "meeting_admins", entry, self.username_lookup, messages, ImportState.WARNING
        )
        return entry, messages

    def count_state(self, state: ImportState) -> int:
        return sum(1 for entry in self.rows if entry["state"] == state)

    def append_message_for_list_fields(
        self, list_names: List[str], template: str, field: str, messages: List[str]
    ) -> None:
        if list_names:
            list_str = ", ".join(list_names)
            object = field.replace("_", " ")[:-1] + "(s)"
            messages.append(template.format(field=object, incorrects=list_str))

    def setup_lookups(self, data: List[Dict[str, Any]]) -> None:
        usernames: Set[str] = set()
        organization_tags: Set[str] = set()
        committee_names: Set[str] = set()
        meeting_template_names: Set[str] = set()

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
            if meeting_template := entry.get("meeting_template"):
                meeting_template_names.add(meeting_template)

        self.committee_lookup = Lookup(
            self.datastore,
            "committee",
            list(committee_names),
            mapped_fields=[
                "forward_to_committee_ids",
                "manager_ids",
                "organization_tag_ids",
            ],
        )
        self.username_lookup = Lookup(
            self.datastore, "user", list(usernames), field="username"
        )
        self.organization_tag_lookup = Lookup(
            self.datastore, "organization_tag", list(organization_tags)
        )
        self.meeting_lookup = Lookup(
            self.datastore, "meeting", list(meeting_template_names)
        )

        self.build_id_lookups_for_remove_check()

    def build_id_lookups_for_remove_check(self) -> None:
        user_ids: Set[int] = set()
        organization_tag_ids: Set[int] = set()
        committee_ids: Set[int] = set()

        for committee_list in self.committee_lookup.name_to_ids.values():
            for committee in committee_list:
                user_ids.update(committee.get("manager_ids") or set())
                organization_tag_ids.update(
                    committee.get("organization_tag_ids") or set()
                )
                committee_ids.update(committee.get("forward_to_committee_ids") or set())
        ids = [
            id_ for id_ in user_ids if id_ not in self.username_lookup.id_to_name.keys()
        ]
        self.username_lookup.read_missing_ids(ids)
        ids = [
            id_
            for id_ in organization_tag_ids
            if id_ not in self.organization_tag_lookup.id_to_name.keys()
        ]
        self.organization_tag_lookup.read_missing_ids(ids)
        ids = [
            id_
            for id_ in committee_ids
            if id_ not in self.committee_lookup.id_to_name.keys()
        ]
        self.committee_lookup.read_missing_ids(ids)

    def fill_committees_to_add_with_pseudo_id(self, data: List[Dict[str, Any]]) -> None:
        for committee in data:
            name = committee["name"]
            if self.committee_lookup.check_duplicate(name) == ResultType.NOT_FOUND:
                self.committee_lookup.name_to_ids[name].append({"id": NEW_COMMITEE_ID})
