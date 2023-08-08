from collections import defaultdict
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
        {"property": "name", "type": "string", "is_object": True},
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

        statistics: Dict[str, int] = defaultdict(int)
        self.import_state = ImportState.DONE
        for entry in self.rows:
            statistics[entry["state"]] += 1
            if entry["state"] == ImportState.ERROR:
                if self.import_state != ImportState.ERROR:
                    self.import_state = ImportState.ERROR
                continue
            if entry["data"].get("meeting_name"):
                if (
                    entry["data"].get("meeting_template")
                    and entry["data"]["meeting_template"]["info"] == ImportState.DONE
                ):
                    statistics["meeting_from_tmpl"] += 1
                else:
                    statistics["meeting_from_create"] += 1

        self.statistics = [
            {"name": "Row errors", "value": statistics.get(ImportState.ERROR, 0)},
            {"name": "Committees created", "value": statistics.get(ImportState.NEW, 0)},
            {
                "name": "Committees updated",
                "value": statistics.get(ImportState.DONE, 0),
            },
            {
                "name": "Meetings created without template",
                "value": statistics.get("meeting_from_create", 0),
            },
            {
                "name": "Meetings copied from template",
                "value": statistics.get("meeting_from_tmpl", 0),
            },
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

        self.store_rows_in_the_action_worker("committee")
        return {}  # do not create any write_requests, this is just for preview

    def validate_entry(
        self,
        entry: Dict[str, Any],
    ) -> Dict[str, Any]:
        messages: List[str] = []

        # committee state handling
        self.import_object_name = entry["name"]
        check_result = self.import_object_lookup.check_duplicate(
            self.import_object_name
        )
        id_ = self.import_object_lookup.get_id_by_name(self.import_object_name)
        if check_result == ResultType.FOUND_ID and id_ != 0:
            self.row_state = ImportState.DONE
            entry["name"] = {
                "value": self.import_object_name,
                "info": ImportState.DONE,
                "id": id_,
            }
        elif check_result == ResultType.NOT_FOUND or id_ == 0:
            self.row_state = ImportState.NEW
            entry["name"] = {"value": self.import_object_name, "info": ImportState.NEW}
        elif check_result == ResultType.FOUND_MORE_IDS:
            self.row_state = ImportState.ERROR
            entry["name"] = {
                "value": self.import_object_name,
                "info": ImportState.ERROR,
            }
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
            self.import_object_lookup,
            messages,
            not_found_state=ImportState.WARNING,
        )
        return {"state": self.row_state, "messages": messages, "data": entry}

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

        self.import_object_lookup = Lookup(
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

        for committee_list in self.import_object_lookup.name_to_ids.values():
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
            if id_ not in self.import_object_lookup.id_to_name.keys()
        ]
        self.import_object_lookup.read_missing_ids(ids)

    def fill_committees_to_add_with_pseudo_id(self, data: List[Dict[str, Any]]) -> None:
        for committee in data:
            name = committee["name"]
            if self.import_object_lookup.check_duplicate(name) == ResultType.NOT_FOUND:
                self.import_object_lookup.name_to_ids[name].append(
                    {"id": NEW_COMMITEE_ID}
                )
