from typing import Any, Dict

from ....models.models import ActionWorker
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...action import Action
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import UserCreate
from .json_upload import ImportStatus
from .user_mixin import DuplicateCheckMixin


@register_action("user.import")
class UserImport(DuplicateCheckMixin, Action):
    """
    Action to import a result from the action_worker.
    """

    model = ActionWorker()
    schema = DefaultSchema(ActionWorker()).get_default_schema(
        additional_required_fields={
            "id": required_id_schema,
        }
    )
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        store_id = instance["id"]
        self.init_duplicate_set()
        worker = self.datastore.get(
            fqid_from_collection_and_id("action_worker", store_id), ["result"]
        )
        action_payload = [
            entry["data"]
            for entry in worker.get("result", {}).get("rows", [])
            if entry["status"] == ImportStatus.CREATE
            and not self.check_for_duplicate(entry["data"]["username"])
        ]
        self.execute_other_action(UserCreate, action_payload)
        return {}

    def handle_relation_updates(self, instance: Dict[str, Any]) -> Any:
        return {}

    def create_events(self, instance: Dict[str, Any]) -> Any:
        return []

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
