from typing import Any, Dict, List, cast

from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ...mixins.import_mixins import (
    BaseImportAction,
    ImportRow,
    ImportState,
    Lookup,
    ResultType,
)
from ...util.register import register_action
from ..agenda_item.agenda_creation import CreateActionWithAgendaItemMixin
from ..agenda_item.update import AgendaItemUpdate
from .create import TopicCreate
from .update import TopicUpdate


@register_action("topic.import")
class TopicImport(BaseImportAction):
    """
    Action to import a result from the import_preview.
    """

    permission = Permissions.AgendaItem.CAN_MANAGE
    import_name = "topic"
    agenda_item_fields = ["agenda_comment", "agenda_duration", "agenda_type"]

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        meeting_id = self.get_meeting_id(instance)
        self.setup_lookups(meeting_id)
        for row in self.rows:
            self.validate_entry(row)

        if self.import_state != ImportState.ERROR:
            create_action_payload: List[Dict[str, Any]] = []
            update_action_payload: List[Dict[str, Any]] = []
            update_agenda_item_payload: List[Dict[str, Any]] = []
            rows = self.flatten_copied_object_fields()
            for row in rows:
                entry = row["data"]
                if row["state"] == ImportState.NEW:
                    create_action_payload.append(entry)
                else:
                    agenda_item = CreateActionWithAgendaItemMixin.remove_agenda_prefix_from_fieldnames(
                        entry
                    )
                    if agenda_item:
                        agenda_item["id"] = self.topic_lookup.get_field_by_name(
                            entry["title"], "agenda_item_id"
                        )
                        update_agenda_item_payload.append(agenda_item)
                    entry.pop("meeting_id", None)
                    update_action_payload.append(entry)
            if create_action_payload:
                self.execute_other_action(TopicCreate, create_action_payload)
            if update_action_payload:
                self.execute_other_action(TopicUpdate, update_action_payload)
            if update_agenda_item_payload:
                self.execute_other_action(AgendaItemUpdate, update_agenda_item_payload)

        return {}

    def validate_entry(self, row: ImportRow) -> None:
        entry = row["data"]
        title = cast(str, self.get_value_from_union_str_object(entry.get("title")))
        check_result = self.topic_lookup.check_duplicate(title)
        id_ = cast(int, self.topic_lookup.get_field_by_name(title, "id"))

        if check_result == ResultType.FOUND_ID and id_ != 0:
            if "id" not in entry:
                raise ActionException(
                    f"Invalid JsonUpload data: A data row with state '{ImportState.DONE}' must have an 'id'"
                )
            elif entry["id"] != id_:
                row["state"] = ImportState.ERROR
                entry["title"]["info"] = ImportState.ERROR
                row["messages"].append(
                    f"Error: topic '{title}' found in different id ({id_} instead of {entry['id']})"
                )
        elif check_result == ResultType.FOUND_MORE_IDS:
            row["state"] = ImportState.ERROR
            entry["title"]["info"] = ImportState.ERROR
            row["messages"].append(f"Error: topic '{title}' is duplicated in import.")
        elif check_result == ResultType.NOT_FOUND_ANYMORE:
            row["messages"].append(
                f"Error: topic {entry['title']['id']} not found anymore for updating topic '{title}'."
            )
            row["state"] = ImportState.ERROR
        elif check_result == ResultType.NOT_FOUND:
            pass  # cannot create an error !

        if row["state"] == ImportState.ERROR and self.import_state == ImportState.DONE:
            self.import_state = ImportState.ERROR

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

    def setup_lookups(self, meeting_id: int) -> None:
        self.topic_lookup = Lookup(
            self.datastore,
            "topic",
            [
                (title, entry["data"])
                for entry in self.rows
                if (title := entry["data"].get("title", {}).get("value"))
            ],
            field="title",
            mapped_fields=["agenda_item_id"],
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )
