from typing import Any, Dict

import fastjsonschema

from ....models.models import Topic
from ....permissions.permissions import Permissions
from ....shared.schema import required_id_schema
from ...mixins.import_mixins import ImportStatus, JsonUploadMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..agenda_item.agenda_creation import agenda_creation_properties
from .create import TopicCreate
from .mixins import DuplicateCheckMixin


@register_action("topic.json_upload")
class TopicJsonUpload(DuplicateCheckMixin, JsonUploadMixin):
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
        {"property": "title", "type": "string"},
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

        # validate and check for duplicates
        self.init_duplicate_set(instance["meeting_id"])
        self.rows = [self.validate_entry(entry) for entry in data]

        # generate statistics
        itemCount = len(self.rows)
        status_to_count = {status: 0 for status in ImportStatus}
        for entry in self.rows:
            status_to_count[entry["status"]] += 1

        self.statistics = [
            {"name": "total", "value": itemCount},
            {"name": "created", "value": status_to_count[ImportStatus.NEW]},
            {"name": "updated", "value": status_to_count[ImportStatus.DONE]},
            {"name": "error", "value": status_to_count[ImportStatus.ERROR]},
            {"name": "warning", "value": status_to_count[ImportStatus.WARNING]},
        ]

        self.set_status(
            status_to_count[ImportStatus.ERROR], status_to_count[ImportStatus.WARNING]
        )
        self.store_rows_in_the_action_worker("topic")
        return {}

    def validate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        status, error = None, []
        try:
            TopicCreate.schema_validator(entry)
            if self.check_for_duplicate(entry["title"]):
                status = ImportStatus.WARNING
            else:
                status = ImportStatus.NEW
        except fastjsonschema.JsonSchemaException as exception:
            status = ImportStatus.ERROR
            error.append(exception.message)
        return {"status": status, "error": error, "data": entry}
