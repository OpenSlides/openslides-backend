from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple

from openslides_backend.action.actions.meeting.mixins import MeetingCheckTimesMixin
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.filters import FilterOperator, Or
from openslides_backend.shared.schema import str_list_schema

from ....models.models import Committee, Meeting
from ....permissions.management_levels import OrganizationManagementLevel
from ...mixins.import_mixins import ImportState, JsonUploadMixin, Lookup, ResultType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("committee.json_upload")
class CommitteeJsonUpload(JsonUploadMixin, MeetingCheckTimesMixin):
    model = Committee()
    schema = DefaultSchema(Committee()).get_default_schema(
        additional_required_fields={
            "data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        **model.get_properties("name", "description"),
                        "forward_to_committees": str_list_schema,
                        "organization_tags": str_list_schema,
                        "committee_managers": str_list_schema,
                        "meeting_name": {"type": "string"},
                        **Meeting().get_properties("start_time", "end_time"),
                        "meeting_admins": str_list_schema,
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
    import_name = "committee"

    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        data = instance.pop("data")
        self.setup_lookups(data)
        self.rows = [self.validate_entry(entry) for entry in data]

        # generate statistics
        itemCount = len(self.rows)
        state_to_count = {state: 0 for state in ImportState}
        for row in self.rows:
            state_to_count[row["state"]] += 1
            state_to_count[ImportState.WARNING] += self.count_warnings_in_payload(
                row.get("data", {}).values()
            )
            row["data"].pop("payload_index", None)

        self.statistics = [
            {"name": "total", "value": itemCount},
            {"name": "created", "value": state_to_count[ImportState.NEW]},
            {"name": "updated", "value": state_to_count[ImportState.DONE]},
            {"name": "error", "value": state_to_count[ImportState.ERROR]},
            {"name": "warning", "value": state_to_count[ImportState.WARNING]},
        ]

        self.set_state(
            state_to_count[ImportState.ERROR], state_to_count[ImportState.WARNING]
        )
        self.store_rows_in_the_import_preview(self.import_name)
        return {}

    def validate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        messages: List[str] = []
        row_state = ImportState.DONE

        # committee state handling
        result = self.committee_lookup.check_duplicate(entry["name"])
        if result == ResultType.FOUND_ID:
            entry["name"] = {
                "value": entry["name"],
                "info": ImportState.DONE,
                "id": self.committee_lookup.get_field_by_name(entry["name"], "id"),
            }
        elif result == ResultType.NOT_FOUND:
            row_state = ImportState.NEW
            entry["name"] = {"value": entry["name"], "info": ImportState.NEW}
        elif result == ResultType.FOUND_MORE_IDS:
            row_state = ImportState.ERROR
            entry["name"] = {
                "value": entry["name"],
                "info": ImportState.ERROR,
            }
            messages.append("Found multiple committees with the same name.")

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
        elif not self.meeting_checks(entry, messages):
            row_state = ImportState.ERROR

        self.validate_with_lookup(
            entry, "committee_managers", self.username_map, messages
        )
        self.validate_with_lookup(
            entry, "forward_to_committees", self.committee_lookup, messages
        )
        self.validate_with_lookup(
            entry, "organization_tags", self.organization_tag_map, messages
        )
        return {"state": row_state, "messages": messages, "data": entry}

    def meeting_checks(self, entry: Dict[str, Any], messages: List[str]) -> bool:
        self.validate_with_lookup(
            entry, "meeting_template", self.meeting_map, messages, is_list=False
        )
        self.validate_with_lookup(entry, "meeting_admins", self.username_map, messages)
        try:
            self.check_start_and_end_time(entry, {})
        except ActionException as e:
            messages.append(e.message)
            return False
        return True

    def validate_with_lookup(
        self,
        entry: Dict[str, Any],
        field: str,
        lookup: Lookup,
        messages: List[str],
        is_list: bool = True,
    ) -> None:
        value = entry.get(field)
        names = [] if not value else value if is_list else [value]
        objects: List[Dict[str, Any]] = []
        missing: List[str] = []
        duplicates: List[str] = []
        for name in names:
            if (result := lookup.check_duplicate(name)) == ResultType.FOUND_ID:
                objects.append(
                    {
                        "value": name,
                        "info": ImportState.DONE,
                        "id": lookup.get_field_by_name(name, "id"),
                    }
                )
            else:
                if result == ResultType.NOT_FOUND and lookup.name_to_ids[name][0]:
                    # the matched committee is currently being imported and therefore has no id
                    objects.append({"value": name, "info": ImportState.DONE})
                else:
                    objects.append({"value": name, "info": ImportState.WARNING})
                    if result == ResultType.NOT_FOUND:
                        missing.append(name)
                    elif result == ResultType.FOUND_MORE_IDS:
                        duplicates.append(name)
        if missing:
            messages.append(
                f"Following values of {field} were not found: '{', '.join(missing)}'"
            )
        if duplicates:
            messages.append(
                f"Following values of {field} could not be uniquely matched: '{', '.join(duplicates)}'"
            )
        if value is not None:
            entry[field] = objects if is_list else objects[0] if objects else None

    def setup_lookups(self, data: List[Dict[str, Any]]) -> None:
        committee_names: Set[str] = set()
        committee_tuples: List[Tuple[str | Tuple[str, ...], Dict[str, Any]]] = []
        usernames: Set[str] = set()
        organization_tags: Set[str] = set()
        forward_committees: Set[str] = set()
        meeting_template_names: Set[str] = set()

        for entry in data:
            committee_names.add(entry["name"])
            committee_tuples.append((entry["name"], entry))
            if forwards := entry.get("forward_to_committees"):
                forward_committees.update(forwards)
            if managers := entry.get("committee_managers"):
                usernames.update(managers)
            if admins := entry.get("meeting_admins"):
                usernames.update(admins)
            if tags := entry.get("organization_tags"):
                organization_tags.update(tags)
            if meeting_template := entry.get("meeting_template"):
                meeting_template_names.add(meeting_template)

        self.committee_lookup = Lookup(
            self.datastore,
            "committee",
            committee_tuples
            + [
                (name, {}) for name in forward_committees if name not in committee_names
            ],
        )
        self.username_map = Lookup(
            self.datastore, "user", [(name, {}) for name in usernames], field="username"
        )
        self.organization_tag_map = Lookup(
            self.datastore,
            "organization_tag",
            [(name, {}) for name in organization_tags],
        )
        self.meeting_map = Lookup(
            self.datastore, "meeting", [(name, {}) for name in meeting_template_names]
        )

    def get_name_map(
        self,
        collection: str,
        entries: List[str],
        fieldname: str = "name",
    ) -> Dict[str, List[int]]:
        lookup: Dict[str, List[int]] = defaultdict(list)
        if len(entries):
            data = self.datastore.filter(
                collection,
                Or([FilterOperator(fieldname, "=", name) for name in set(entries)]),
                ["id", fieldname],
                lock_result=False,
            )
            for date in data.values():
                lookup[date[fieldname]].append(date["id"])
        return lookup
