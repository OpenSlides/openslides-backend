from typing import Any

from ....permissions.permissions import Permissions
from ....shared.patterns import fqid_from_collection_and_id
from ...mixins.import_mixins import BaseImportAction, ImportState
from ...util.register import register_action
from .create import TopicCreate


@register_action("topic.import")
class TopicImport(BaseImportAction):
    """
    Action to import a result from the import_preview.
    """

    permission = Permissions.AgendaItem.CAN_MANAGE
    import_name = "topic"
    agenda_item_fields = ["agenda_comment", "agenda_duration", "agenda_type"]

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)

        if self.import_state != ImportState.ERROR:
            create_action_payload: list[dict[str, Any]] = []
            rows = self.flatten_copied_object_fields()
            for row in rows:
                create_action_payload.append(row["data"])
            if create_action_payload:
                self.execute_other_action(TopicCreate, create_action_payload)

        return {}

    def get_meeting_id(self, instance: dict[str, Any]) -> int:
        store_id = instance["id"]
        worker = self.datastore.get(
            fqid_from_collection_and_id("import_preview", store_id),
            ["name", "result"],
            lock_result=False,
        )
        if worker.get("name") == TopicImport.import_name:
            return next(iter(worker.get("result", {})["rows"]))["data"]["meeting_id"]
