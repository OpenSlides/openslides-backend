from typing import Any, Dict, List

from ....models.models import Topic
from ....permissions.permissions import Permissions
from ....shared.filters import FilterOperator
from ....shared.schema import required_id_schema
from ...mixins.import_mixins import ImportState, JsonUploadMixin, Lookup, ResultType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..agenda_item.agenda_creation import agenda_creation_properties


@register_action("topic.json_upload")
class TopicJsonUpload(JsonUploadMixin):
    """
    Action to allow to upload a json. It is used as first step of an import.
    """

    model = Topic()
    schema = DefaultSchema(Topic()).get_default_schema(
        additional_required_fields={
            "data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        **model.get_properties("title", "text"),
                        **{
                            prop: agenda_creation_properties[prop]
                            for prop in (
                                "agenda_comment",
                                "agenda_type",
                                "agenda_duration",
                            )
                        },
                    },
                    "required": ["title"],
                    "additionalProperties": False,
                },
                "minItems": 1,
                "uniqueItems": False,
            },
            "meeting_id": required_id_schema,
        }
    )
    permission = Permissions.AgendaItem.CAN_MANAGE
    headers = [
        {"property": "title", "type": "string", "is_object": True},
        {"property": "text", "type": "string"},
        {"property": "agenda_comment", "type": "string"},
        {"property": "agenda_type", "type": "string"},
        {"property": "agenda_duration", "type": "integer"},
    ]

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        data = instance.pop("data")

        # enrich data with meeting_id
        for entry in data:
            entry["meeting_id"] = instance["meeting_id"]

        # setup and validate entries
        self.setup_lookups(data, instance["meeting_id"])
        self.rows = [self.validate_entry(entry) for entry in data]

        # generate statistics
        itemCount = len(self.rows)
        state_to_count = {state: 0 for state in ImportState}
        for entry in self.rows:
            state_to_count[entry["state"]] += 1

        self.statistics = [
            {"name": "total", "value": itemCount},
            {"name": "created", "value": state_to_count[ImportState.NEW]},
            {"name": "updated", "value": state_to_count[ImportState.DONE]},
            {"name": "error", "value": state_to_count[ImportState.ERROR]},
            {"name": "warning", "value": state_to_count[ImportState.WARNING]},
        ]

        # finalize
        self.set_state(
            state_to_count[ImportState.ERROR], state_to_count[ImportState.WARNING]
        )
        self.store_rows_in_the_import_preview("topic")
        return {}

    def validate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        state, messages = None, []
        check_result = self.topic_lookup.check_duplicate(entry["title"])
        if check_result == ResultType.FOUND_ID:
            state = ImportState.WARNING
            messages.append("Duplicate, import will update this topic.")
            entry["title"] = {
                "value": entry["title"],
                "info": ImportState.DONE,
                "id": self.topic_lookup.get_field_by_name(entry["title"], "id"),
            }
        elif check_result == ResultType.NOT_FOUND:
            state = ImportState.NEW
            entry["title"] = {"value": entry["title"], "info": ImportState.NEW}
        elif check_result == ResultType.FOUND_MORE_IDS:
            state = ImportState.ERROR
            entry["title"] = {"value": entry["title"], "info": ImportState.ERROR}
        return {"state": state, "messages": messages, "data": entry}

    def setup_lookups(self, data: List[Dict[str, Any]], meeting_id: int) -> None:
        self.topic_lookup = Lookup(
            self.datastore,
            "topic",
            [(title, entry) for entry in data if (title := entry.get("title"))],
            field="title",
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )
