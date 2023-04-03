from enum import Enum
from time import time
from typing import Any, Dict, Optional

import fastjsonschema

from ....models.models import Topic
from ....permissions.permissions import Permissions
from ....shared.interfaces.event import Event, EventType
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...action import Action
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionResultElement
from ..agenda_item.agenda_creation import agenda_creation_properties
from .create import TopicCreate
from .mixins import DuplicateCheckMixin


class ImportStatus(str, Enum):
    NEW = "new"
    ERROR = "error"
    DONE = "done"


@register_action("topic.json_upload")
class TopicJsonUpload(DuplicateCheckMixin, Action):
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
        {"proptery": "agenda_duration", "type": "number"},
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
        itemCount, itemNew, itemError = 0, 0, 0
        for entry in self.rows:
            itemCount += 1
            if entry["status"] == ImportStatus.NEW:
                itemNew += 1
            if entry["status"] == ImportStatus.ERROR:
                itemError += 1
        self.statistics = {
            "total": itemCount,
            "created": itemNew,
            "omitted": itemError,
        }

        # store rows in the action_worker
        self.new_store_id = self.datastore.reserve_id(collection="action_worker")
        fqid = fqid_from_collection_and_id("action_worker", self.new_store_id)
        time_created = int(time())
        self.datastore.write_action_worker(
            WriteRequest(
                events=[
                    Event(
                        type=EventType.Create,
                        fqid=fqid,
                        fields={
                            "id": self.new_store_id,
                            "result": {"import": "topic", "rows": self.rows},
                            "created": time_created,
                            "timestamp": time_created,
                            "state": "running",
                        },
                    )
                ],
                user_id=self.user_id,
                locked_fields={},
            )
        )
        return {}

    def validate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        status, error = None, []
        try:
            TopicCreate.schema_validator(entry)
            if self.check_for_duplicate(entry["title"]):
                status = ImportStatus.ERROR
                error.append("Duplicate")
            else:
                status = ImportStatus.NEW
        except fastjsonschema.JsonSchemaException as exception:
            status = ImportStatus.ERROR
            error.append(exception.message)
        return {"status": status, "error": error, "data": entry}

    def handle_relation_updates(self, instance: Dict[str, Any]) -> Any:
        return {}

    def create_events(self, instance: Dict[str, Any]) -> Any:
        return []

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        return {
            "id": self.new_store_id,
            "headers": self.headers,
            "rows": self.rows,
            "statistics": self.statistics,
        }
