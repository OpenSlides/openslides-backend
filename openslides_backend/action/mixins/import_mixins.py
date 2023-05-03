from enum import Enum
from time import time
from typing import Any, Callable, Dict, List, Optional, TypedDict

from ...shared.exceptions import ActionException
from ...shared.interfaces.event import Event, EventType
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import fqid_from_collection_and_id
from ..action import Action
from ..util.typing import ActionData, ActionResultElement


class ImportStatus(str, Enum):
    ERROR = "error"
    NEW = "new"
    WARNING = "warning"
    DONE = "done"
    GENERATED = "generated"


class ImportMixin(Action):
    """
    Mixin for import actions. It works together with the json_upload.
    """

    def handle_relation_updates(self, instance: Dict[str, Any]) -> Any:
        return {}

    def create_events(self, instance: Dict[str, Any]) -> Any:
        return []

    def get_on_success(self, action_data: ActionData) -> Callable[[], None]:
        def on_success() -> None:
            for instance in action_data:
                store_id = instance["id"]
                self.datastore.write_action_worker(
                    WriteRequest(
                        events=[
                            Event(
                                type=EventType.Delete,
                                fqid=fqid_from_collection_and_id(
                                    "action_worker", store_id
                                ),
                            )
                        ],
                        user_id=self.user_id,
                        locked_fields={},
                    )
                )

        return on_success


class HeaderEntry(TypedDict):
    property: str
    type: str


class JsonUploadMixin(Action):
    headers: List[HeaderEntry]
    rows: List[Dict[str, Any]]
    statistics: Any

    def store_rows_in_the_action_worker(self, import_name: str) -> None:
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
                            "result": {"import": import_name, "rows": self.rows},
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

    def validate_instance(self, instance: Dict[str, Any]) -> None:
        # filter extra, not needed fields before validate and parse some fields
        property_to_type = {
            header["property"]: header["type"] for header in self.headers
        }
        for entry in list(instance.get("data", [])):
            for field in dict(entry):
                if field not in property_to_type:
                    del entry[field]
                else:
                    type_ = property_to_type[field]
                    if type_ == "integer":
                        try:
                            entry[field] = int(entry[field])
                        except ValueError:
                            raise ActionException(
                                f"Could not parse {entry[field]} expect integer"
                            )
                    elif type_ == "boolean":
                        if entry[field] in ("1", "true", "True", "T", "t"):
                            entry[field] = True
                        elif entry[field] in ("0", "false", "False", "F", "f"):
                            entry[field] = False
                        else:
                            raise ActionException(
                                f"Could not parse {entry[field]} expect boolean"
                            )

        super().validate_instance(instance)
