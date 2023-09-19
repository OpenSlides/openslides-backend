from typing import Any, Dict, List

from ....models.models import ImportPreview
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...mixins.import_mixins import ImportMixin, ImportState, Lookup, ResultType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import TopicCreate


@register_action("topic.import")
class TopicImport(ImportMixin):
    """
    Action to import a result from the import_preview.
    """

    model = ImportPreview()
    schema = DefaultSchema(ImportPreview()).get_default_schema(
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
        self.setup_lookups(self.result.get("rows", []), meeting_id)
        action_payload = [
            entry["data"]
            for entry in self.result.get("rows", [])
            if (entry["state"] in (ImportState.NEW, ImportState.WARNING))
            and self.topic_lookup.check_duplicate(entry["data"]["title"]["value"])
            == ResultType.NOT_FOUND
        ]
        for entry in action_payload:
            entry["title"] = entry["title"]["value"]
        self.execute_other_action(TopicCreate, action_payload)
        self.error = False
        return instance

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        store_id = instance["id"]
        worker = self.datastore.get(
            fqid_from_collection_and_id("import_preview", store_id),
            ["name", "result"],
            lock_result=False,
        )
        if worker.get("name") == TopicImport.import_name:
            return next(iter(worker.get("result", {})["rows"]))["data"]["meeting_id"]
        raise ActionException("Import data cannot be found.")

    def setup_lookups(self, data: List[Dict[str, Any]], meeting_id: int) -> None:
        self.topic_lookup = Lookup(
            self.datastore,
            "topic",
            [
                (title, entry["data"])
                for entry in data
                if (title := entry["data"].get("title", {}).get("value"))
            ],
            field="title",
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )
