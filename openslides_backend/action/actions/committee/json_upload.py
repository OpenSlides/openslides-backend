from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from openslides_backend.action.actions.meeting.mixins import MeetingCheckTimesMixin
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.filters import And, Filter, FilterOperator, Or
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
                        "managers": str_list_schema,
                        **{
                            f"meeting_{field}": prop
                            for field, prop in Meeting()
                            .get_properties("name", "start_time", "end_time")
                            .items()
                        },
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
            "property": "managers",
            "type": "string",
            "is_object": True,
            "is_list": True,
        },
        {"property": "meeting_name", "type": "string"},
        {"property": "meeting_start_time", "type": "date"},
        {"property": "meeting_end_time", "type": "date"},
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

        # check meeting_template afterwards to ensure each committee has an id
        self.check_meetings()

        self.generate_statistics()
        return {}

    def validate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        messages: List[str] = []
        row_state = ImportState.DONE

        # committee state handling
        result = self.committee_lookup.check_duplicate(entry["name"])
        if result == ResultType.FOUND_ID:
            id = self.committee_lookup.get_field_by_name(entry["name"], "id")
            entry["name"] = {
                "value": entry["name"],
                "info": ImportState.DONE,
                "id": id,
            }
            entry["id"] = id
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
                    "meeting_start_time",
                    "meeting_end_time",
                    "meeting_admins",
                    "meeting_template",
                )
            ):
                messages.append("No meeting will be created without meeting_name")
        else:
            self.validate_with_lookup(
                entry, "meeting_admins", self.username_lookup, messages
            )
            try:
                self.check_start_and_end_time(
                    {
                        field: entry[meeting_field]
                        for field in ("start_time", "end_time")
                        if (meeting_field := f"meeting_{field}") in entry
                    },
                    {},
                )
            except ActionException as e:
                messages.append(e.message)
                row_state = ImportState.ERROR

        self.validate_with_lookup(entry, "managers", self.username_lookup, messages)
        self.validate_with_lookup(
            entry, "forward_to_committees", self.committee_lookup, messages
        )
        self.validate_with_lookup(
            entry,
            "organization_tags",
            self.organization_tag_lookup,
            messages,
            create=True,
        )
        return {"state": row_state, "messages": messages, "data": entry}

    def check_meetings(self) -> None:
        # search for relevant meetings in datastore
        filters: List[Filter] = []
        for row in self.rows:
            entry = row["data"]
            if (committee_id := entry["name"].get("id")) and (
                meeting_name := entry.get("meeting_name")
            ):
                # find meeting duplicates by name and time
                parts = [
                    FilterOperator("committee_id", "=", committee_id),
                    FilterOperator("name", "=", meeting_name),
                ]
                for field in ("start_time", "end_time"):
                    if time := entry.get(f"meeting_{field}"):
                        start_of_day = datetime.fromtimestamp(time, timezone.utc)
                        start_of_day.replace(hour=0, minute=0, second=0, microsecond=0)
                        end_of_day = start_of_day + timedelta(days=1)
                        parts.extend(
                            (
                                FilterOperator(field, ">=", start_of_day.timestamp()),
                                FilterOperator(field, "<", end_of_day.timestamp()),
                            )
                        )
                    else:
                        parts.append(FilterOperator(field, "=", None))
                filters.append(And(*parts))
                # find template meetings
                if template_name := entry.get("meeting_template"):
                    filters.append(
                        And(
                            FilterOperator("name", "=", template_name),
                            FilterOperator("committee_id", "=", committee_id),
                        )
                    )
        results = (
            self.datastore.filter(
                "meeting",
                Or(*filters),
                ["id", "name", "committee_id", "start_time", "end_time"],
                lock_result=False,
                use_changed_models=False,
            )
            if len(filters)
            else {}
        )
        meeting_map = defaultdict(list)
        for meeting in results.values():
            meeting_map[(meeting["name"], meeting["committee_id"])].append(meeting)

        for row in self.rows:
            entry = row["data"]
            # check for duplicate meeting
            if (committee_id := entry["name"].get("id")) and (
                meeting_name := entry.get("meeting_name")
            ):
                meetings = meeting_map[(meeting_name, committee_id)]
                for meeting in meetings:
                    if all(
                        self.is_same_day(
                            entry.get(f"meeting_{field}"), meeting.get(field)
                        )
                        for field in ("start_time", "end_time")
                    ):
                        row["messages"].append(
                            "A meeting with this name and dates already exists."
                        )
                        row["state"] = ImportState.ERROR
                        break

            # check template meeting
            if template := entry.pop("meeting_template", None):
                entry["meeting_template"] = {
                    "value": template,
                    "info": ImportState.WARNING,
                }
                if not committee_id:
                    row["messages"].append(
                        "Template meetings can only be used for existing committees."
                    )
                elif not entry.get("meeting_name"):
                    pass  # message was already created in meeting_checks
                else:
                    meetings = meeting_map[(template, committee_id)]
                    if len(meetings) > 1:
                        row["messages"].append(
                            "Found multiple meetings with given template name, the meeting will be created without a template."
                        )
                    elif len(meetings) == 1:
                        entry["meeting_template"].update(
                            {
                                "id": meetings[0]["id"],
                                "info": ImportState.DONE,
                            }
                        )
                    else:
                        row["messages"].append(
                            f"The meeting template {template} was not found, the meeting will be created without a template."
                        )

    def is_same_day(self, a: Optional[int], b: Optional[int]) -> bool:
        if a is None or b is None:
            return a == b
        dt_a = datetime.fromtimestamp(a, timezone.utc)
        dt_b = datetime.fromtimestamp(b, timezone.utc)
        return dt_a.date() == dt_b.date()

    def validate_with_lookup(
        self,
        entry: Dict[str, Any],
        field: str,
        lookup: Lookup,
        messages: List[str],
        create: bool = False,
    ) -> None:
        names = entry.get(field, [])
        objects: List[Dict[str, Any]] = []
        missing: List[str] = []
        duplicates: List[str] = []
        for name in names:
            obj = {"value": name, "info": ImportState.DONE}
            if (result := lookup.check_duplicate(name)) == ResultType.FOUND_ID:
                obj["id"] = lookup.get_field_by_name(name, "id")
            else:
                if result == ResultType.NOT_FOUND:
                    if lookup.name_to_ids[name][0]:
                        # the matched committee is currently being imported and therefore has no id
                        pass
                    elif create:
                        obj["info"] = ImportState.NEW
                    else:
                        obj["info"] = ImportState.WARNING
                        missing.append(name)
                elif result == ResultType.FOUND_MORE_IDS:
                    duplicates.append(name)
            objects.append(obj)
        if missing:
            messages.append(
                f"Following values of {field} were not found: '{', '.join(missing)}'"
            )
        if duplicates:
            messages.append(
                f"Following values of {field} could not be uniquely matched: '{', '.join(duplicates)}'"
            )
        if names:
            entry[field] = objects

    def generate_statistics(self) -> None:
        super().generate_statistics()
        statistics_data = {
            "meetings_created": 0,
            "meetings_cloned": 0,
            "organization_tags_created": 0,
        }
        for row in self.rows:
            entry = row["data"]
            if entry.get("meeting_name"):
                if (
                    entry.get("meeting_template")
                    and entry["meeting_template"]["info"] == ImportState.DONE
                ):
                    statistics_data["meetings_cloned"] += 1
                else:
                    statistics_data["meetings_created"] += 1
            for tag in entry.get("organization_tags", []):
                if tag["info"] == ImportState.NEW:
                    statistics_data["organization_tags_created"] += 1
        self.statistics.extend(
            {"name": key, "value": value} for key, value in statistics_data.items()
        )

    def setup_lookups(self, data: List[Dict[str, Any]]) -> None:
        committee_names: Set[str] = set()
        committee_tuples: List[Tuple[str | Tuple[str, ...], Dict[str, Any]]] = []
        usernames: Set[str] = set()
        organization_tags: Set[str] = set()
        forward_committees: Set[str] = set()

        for entry in data:
            committee_names.add(entry["name"])
            committee_tuples.append((entry["name"], entry))
            if forwards := entry.get("forward_to_committees"):
                forward_committees.update(forwards)
            if managers := entry.get("managers"):
                usernames.update(managers)
            if admins := entry.get("meeting_admins"):
                usernames.update(admins)
            if tags := entry.get("organization_tags"):
                organization_tags.update(tags)

        self.committee_lookup = Lookup(
            self.datastore,
            "committee",
            committee_tuples
            + [
                (name, {}) for name in forward_committees if name not in committee_names
            ],
        )
        self.username_lookup = Lookup(
            self.datastore, "user", [(name, {}) for name in usernames], field="username"
        )
        self.organization_tag_lookup = Lookup(
            self.datastore,
            "organization_tag",
            [(name, {}) for name in organization_tags],
        )
