from enum import Enum
from time import time
from typing import Any, Callable, Dict, List, Optional

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


class JsonUploadMixin(Action):
    headers: Any

    def init_rows(self, rows: List[Dict[str, Any]]) -> None:
        self.rows = rows

        # generate statistics
        itemCount, itemNew, itemDone, itemError = len(self.rows), 0, 0, 0
        itemWarning = 0
        for entry in self.rows:
            if entry["status"] == ImportStatus.NEW:
                itemNew += 1
            elif entry["status"] == ImportStatus.DONE:
                itemDone += 1
            elif entry["status"] == ImportStatus.ERROR:
                itemError += 1
            elif entry["status"] == ImportStatus.WARNING:
                itemWarning += 1
        self.statistics = {
            "total": itemCount,
            "created": itemNew,
            "updated": itemDone,
            "omitted": itemError,
            "warning": itemWarning,
        }

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
