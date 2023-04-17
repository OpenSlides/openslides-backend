from enum import Enum
from typing import Any, Callable, Dict

from ...shared.interfaces.event import Event, EventType
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import fqid_from_collection_and_id
from ..action import Action
from ..util.typing import ActionData


class ImportStatus(str, Enum):
    ERROR = "error"
    CREATE = "create"
    UPDATE = "update"


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
