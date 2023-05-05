from typing import Any, Dict

from ....models.models import ActionWorker
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...mixins.import_mixins import ImportMixin, ImportState
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import TopicCreate
from .mixins import DuplicateCheckMixin


@register_action("topic.import")
class TopicImport(DuplicateCheckMixin, ImportMixin):
    """
    Action to import a result from the action_worker.
    """

    model = ActionWorker()
    schema = DefaultSchema(ActionWorker()).get_default_schema(
        additional_required_fields={
            "id": required_id_schema,
            "import": {"type": "boolean"},
        }
    )
    permission = Permissions.AgendaItem.CAN_MANAGE
    import_name = "topic"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)

        # handle abort in on_success
        if not instance["import"]:
            return {}

        meeting_id = self.get_meeting_id(instance)
        self.init_duplicate_set(meeting_id)
        action_payload = [
            entry["data"]
            for entry in self.result.get("rows", [])
            if (entry["state"] in (ImportState.NEW, ImportState.WARNING))
            and not self.check_for_duplicate(entry["data"]["title"])
        ]
        self.execute_other_action(TopicCreate, action_payload)
        self.error = False
        return instance

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        store_id = instance["id"]
        worker = self.datastore.get(
            fqid_from_collection_and_id("action_worker", store_id),
            ["result"],
            lock_result=False,
        )
        if worker.get("result", {}).get("import") == TopicImport.import_name:
            return next(iter(worker["result"]["rows"]))["data"]["meeting_id"]
        raise ActionException("Import data cannot be found.")
