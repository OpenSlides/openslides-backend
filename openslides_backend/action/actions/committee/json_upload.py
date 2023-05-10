from typing import Any, Dict

from ....models.models import Committee
from ....permissions.management_levels import OrganizationManagementLevel
from ...mixins.import_mixins import ImportState, JsonUploadMixin, Lookup
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
                        "meeting_name": {"type": "string"},
                        "start_date": {"type": "integer"},
                        "end_date": {"type": "integer"},
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
        {"property": "meeting_name", "type": "string"},
        {"property": "start_date", "type": "date"},
        {"property": "end_date", "type": "date"},
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
        self.rows = [
            self.validate_entry(entry, duplicate_checker, meeting_lookup)
            for entry in data
        ]
        self.statistics = []
        self.set_state(0, 0)
        self.store_rows_in_the_action_worker("committee")
        return {}

    def validate_entry(
        self, entry: Dict[str, Any], duplicate_checker: Lookup, meeting_lookup: Lookup
    ) -> Dict[str, Any]:
        state, messages = None, []
        if duplicate_checker.check_duplicate(entry["name"]):
            state = ImportState.DONE
            if committee_id := duplicate_checker.get_id_by_name(entry["name"]):
                entry["id"] = committee_id
            else:
                state = ImportState.ERROR
                messages.append("Found name and didn't found id.")
        else:
            state = ImportState.NEW
        if "start_date" in entry or "end_date" in entry:
            if "meeting_name" not in entry:
                state = ImportState.ERROR
                messages.append("Start_date or end_date given, but no meeting_name")
        if "meeting_template" in entry:
            if meeting_id := meeting_lookup.get_id_by_name(entry["meeting_template"]):
                entry["meeting_template"] = {
                    "value": entry["meeting_template"],
                    "info": ImportState.DONE,
                    "id": meeting_id,
                }
            else:
                entry["meeting_template"] = {
                    "value": entry["meeting_template"],
                    "info": ImportState.WARNING,
                }
        return {"state": state, "messages": messages, "data": entry}
