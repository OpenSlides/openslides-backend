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
from ..agenda_item.update import AgendaItemUpdate
from .create import TopicCreate
from .update import TopicUpdate


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
        create_payloads = [
            entry["data"]
            for entry in self.result.get("rows", [])
            if entry["state"] == ImportState.NEW
            and self.topic_lookup.check_duplicate(entry["data"]["title"]["value"])
            == ResultType.NOT_FOUND
        ]
        pre_update_payloads = [
            entry["data"]
            for entry in self.result.get("rows", [])
            if entry["state"] == ImportState.WARNING
            and self.topic_lookup.check_duplicate(entry["data"]["title"]["value"])
            == ResultType.FOUND_ID
            and entry["data"]["title"].get("id")
            == self.topic_lookup.get_field_by_name(
                entry["data"]["title"]["value"], "id"
            )
        ]
        update_payloads: List[Dict[str, Any]] = []
        agenda_item_updates: List[Dict[str, Any]] = []
        for entry in create_payloads:
            entry["title"] = entry["title"]["value"]
        for entry in pre_update_payloads:
            if entry.get("text"):
                update_payloads.append(
                    {"id": entry["title"]["id"], "text": entry["text"]}
                )
            agenda_item: Dict[str, Any] = {}
            for field in (
                "agenda_comment",
                "agenda_type",
                "agenda_duration",
            ):
                if entry.get(field):
                    agenda_item[field[7:]] = entry[field]
            if agenda_item:
                agenda_item["id"] = self.topic_lookup.get_field_by_name(
                    entry["title"]["value"], "agenda_item_id"
                )
                agenda_item_updates.append(agenda_item)

        if create_payloads:
            self.execute_other_action(TopicCreate, create_payloads)
        if update_payloads:
            self.execute_other_action(TopicUpdate, update_payloads)
        if agenda_item_updates:
            self.execute_other_action(AgendaItemUpdate, agenda_item_updates)
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
            mapped_fields=["agenda_item_id"],
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )
