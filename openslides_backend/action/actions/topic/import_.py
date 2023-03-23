from typing import Any, Dict

from ....models.models import ActionWorker
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...action import Action
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import TopicCreate
from .mixins import DuplicateCheckMixin


@register_action("topic.import")
class TopicImport(DuplicateCheckMixin, Action):
    """
    Action to import a result from the action_worker.
    """

    model = ActionWorker()
    schema = DefaultSchema(ActionWorker()).get_default_schema(
        additional_required_fields={
            "id": required_id_schema,
        }
    )
    permission = Permissions.AgendaItem.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        store_id = instance["id"]
        meeting_id = self.get_meeting_id(instance)
        self.init_duplicate_set(meeting_id)
        worker = self.datastore.get(
            fqid_from_collection_and_id("action_worker", store_id), ["result"]
        )
        action_payload = [
            entry["data"]
            for entry in worker.get("result", {}).get("rows", [])
            if entry["status"] == "new"
            and not self.check_for_duplicate(entry["data"]["title"])
        ]
        self.execute_other_action(TopicCreate, action_payload)
        return {}

    def handle_relation_updates(self, instance: Dict[str, Any]) -> Any:
        return {}

    def create_events(self, instance: Dict[str, Any]) -> Any:
        return []

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        store_id = instance["id"]
        worker = self.datastore.get(
            fqid_from_collection_and_id("action_worker", store_id), ["result"]
        )
        if worker.get("result", {}).get("import") == "topic":
            return next(iter(worker["result"]["rows"]))["data"]["meeting_id"]
        raise ActionException("Import data cannot be found.")
