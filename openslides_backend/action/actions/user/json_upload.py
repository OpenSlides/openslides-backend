from enum import Enum
from typing import Any, Dict, Optional

import fastjsonschema

from ....models.models import User
from ....shared.interfaces.event import Event, EventType
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import fqid_from_collection_and_id
from ...action import Action
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionResultElement
from .create import UserCreate
from .user_mixin import DuplicateCheckMixin


class ImportStatus(str, Enum):
    NEW = "new"
    ERROR = "error"
    DONE = "done"


@register_action("user.json_upload")
class UserJsonUpload(DuplicateCheckMixin, Action):
    """
    Action to allow to upload a json. It is used as first step of an import.
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        additional_required_fields={
            "data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        **model.get_properties(
                            "title",
                            "first_name",
                            "last_name",
                            "is_active",
                            "is_physical_person",
                            "default_password",
                            "email",
                            "username",
                            "gender",
                            "pronoun",
                        ),
                    },
                    "required": ["username"],
                    "additionalProperties": False,
                },
                "minItems": 1,
                "uniqueItems": False,
            },
        }
    )
    headers = [
        {"property": "title", "type": "string"},
        {"property": "first_name", "type": "string"},
        {"property": "last_name", "type": "string"},
        {"property": "is_active", "type": "boolean"},
        {"property": "is_physical_person", "type": "boolean"},
        {"property": "default_password", "type": "string"},
        {"property": "email", "type": "string"},
        {"property": "username", "type": "string"},
        {"property": "gender", "type": "string"},
        {"property": "pronoun", "type": "string"},
    ]
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        data = instance.pop("data")

        # validate and check for duplicates
        self.init_duplicate_set()
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
        self.datastore.write_action_worker(
            WriteRequest(
                events=[
                    Event(
                        type=EventType.Create,
                        fqid=fqid,
                        fields={
                            "id": self.new_store_id,
                            "result": {"import": "account", "rows": self.rows},
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
            UserCreate.schema_validator(entry)
            if self.check_for_duplicate(entry["username"]):
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

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
