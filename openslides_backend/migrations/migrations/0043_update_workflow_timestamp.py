from typing import Any, Dict, List, Optional, Tuple

from datastore.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    DeleteFieldsEvent,
    UpdateEvent,
)
from datastore.shared.util import collection_from_fqid


class Migration(BaseEventMigration):
    """
    This migration renames set_created_timestamp and copy created.
    """

    target_migration_index = 44
    collection_to_old_and_new_field_and_type = {
        "motion_state": [
            ("set_created_timestamp", "set_workflow_timestamp", "rename"),
        ],
        "motion": [
            ("created", "workflow_timestamp", "copy"),
        ],
    }

    def modify(
        self, object: Dict[str, Any], fields: List[Tuple[str, str, str]]
    ) -> None:
        for old_field, new_field, type_ in fields:
            if old_field in object:
                object[new_field] = object[old_field]
                if type_ == "rename":
                    del object[old_field]

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection = collection_from_fqid(event.fqid)
        if collection not in self.collection_to_old_and_new_field_and_type:
            return None

        if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
            self.modify(
                event.data, self.collection_to_old_and_new_field_and_type[collection]
            )

        elif isinstance(event, DeleteFieldsEvent):
            for (
                old_field,
                new_field,
                type_,
            ) in self.collection_to_old_and_new_field_and_type[collection]:
                if old_field in event.data:
                    if type_ == "rename":
                        event.data.remove(old_field)
                    event.data.append(new_field)

        return [event]
