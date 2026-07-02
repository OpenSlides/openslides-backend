from typing import Any

from ....models.models import Topic
from ....permissions.permissions import Permissions
from ....shared.schema import required_id_schema
from ...mixins.import_mixins import BaseJsonUploadAction, ImportState, Lookup
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

        # setup and blanket validate entries
        self.rows = [self.validate_entry(entry) for entry in data]

        self.generate_statistics()
        return {}

    def validate_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        entry["title"] = {"value": entry["title"], "info": ImportState.NEW}
        return {"state": ImportState.NEW, "messages": [], "data": entry}
