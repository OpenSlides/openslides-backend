from typing import Any

from ....models.models import Topic
from ....permissions.permissions import Permissions
from ....shared.filters import FilterOperator
from ....shared.schema import required_id_schema
from ...mixins.import_mixins import (
    BaseJsonUploadAction,
    ImportState,
    Lookup,
    ResultType,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..agenda_item.agenda_creation import agenda_creation_properties


@register_action("topic.json_upload")
class TopicJsonUpload(BaseJsonUploadAction):
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
    headers = [
        {"property": "title", "type": "string", "is_object": True},
        {"property": "text", "type": "string"},
        {"property": "agenda_comment", "type": "string"},
        {"property": "agenda_type", "type": "string"},
        {"property": "agenda_duration", "type": "integer"},
    ]
    permission = Permissions.AgendaItem.CAN_MANAGE
    import_name = "topic"
    row_state: ImportState
    topic_lookup: Lookup

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        data = instance.pop("data")

        # enrich data with meeting_id
        for entry in data:
            entry["meeting_id"] = instance["meeting_id"]

        # setup and validate entries
        self.setup_lookups(data, instance["meeting_id"])
        self.rows = [self.validate_entry(entry) for entry in data]

        self.generate_statistics()
        return {}

    def validate_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        state, messages = None, []
        check_result = self.topic_lookup.check_duplicate(title := entry["title"])
        id_ = self.topic_lookup.get_field_by_name(title, "id")
        if check_result == ResultType.FOUND_ID:
            state = ImportState.DONE
            messages.append("Existing topic will be updated.")
            entry["id"] = id_
            entry["title"] = {
                "value": title,
                "info": ImportState.WARNING,
                "id": id_,
            }
        elif check_result == ResultType.NOT_FOUND:
            state = ImportState.NEW
            entry["title"] = {"value": title, "info": ImportState.NEW}
        elif check_result == ResultType.FOUND_MORE_IDS:
            state = ImportState.ERROR
            messages.append(f"Duplicated topic name '{title}'.")
            entry["title"] = {"value": title, "info": ImportState.ERROR}
        return {"state": state, "messages": messages, "data": entry}

    def setup_lookups(self, data: list[dict[str, Any]], meeting_id: int) -> None:
        self.topic_lookup = Lookup(
            self.datastore,
            "topic",
            [(title, entry) for entry in data if (title := entry.get("title"))],
            field="title",
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )
