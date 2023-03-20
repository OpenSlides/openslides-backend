from typing import Any, Dict

import fastjsonschema

from ....models.models import Topic
from ....shared.schema import required_id_schema
from ...action import Action
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import TopicCreate


@register_action("topic.json_upload")
class TopicJsonUpload(Action):
    """
    Action to allow to upload a json. It is used as first step of an import.
    """

    model = Topic()
    schema = DefaultSchema(Topic()).get_default_schema(
        additional_required_fields={
            "data": {
                "type": "array",
                "items": {"type": "object"},
                "minItems": 1,
                "uniqueItems": True,
            },
            "meeting_id": required_id_schema,
        }
    )
    # permission = ???
    whitelist = [
        "title",
        "meeting_id",
        "text",
        "attachment_ids",
        "agenda_create",
        "agenda_type",
        "agenda_parent_id",
        "agenda_comment",
        "agenda_duration",
        "agenda_weight",
    ]

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        data = instance.pop("data")

        # filter fields not in the whitelist
        data = [
            {field: partial[field] for field in self.whitelist if field in partial}
            for partial in data
        ]

        # special code for agenda_type and agenda_duration
        for entry in data:
            if "agenda_type" in entry:
                entry["agenda_type"] = self.update_agenda_type(entry["agenda_type"])
            if "agenda_duration" in entry:
                entry["agenda_duration"] = self.update_agenda_duration(
                    entry["agenda_duration"]
                )

        # validate
        preview_data = [self.validate_entry(entry) for entry in data]
        print("XXX", preview_data)
        return {}

    def update_agenda_type(self, value: Any) -> int:
        return 1

    def update_agenda_duration(self, value: Any) -> int:
        return 10

    def validate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        okay, error = None, None
        try:
            TopicCreate.schema_validator(entry)
            okay = True
        except fastjsonschema.JsonSchemaException as exception:
            okay = False
            error = exception.message
        preview_entry = {"okay": okay, "entry": entry}
        if error:
            preview_entry["error"] = error
        return preview_entry

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        # ???
        pass

    def handle_relation_updates(self, instance: Dict[str, Any]) -> Any:
        return {}

    def create_events(self, instance: Dict[str, Any]) -> Any:
        return []
