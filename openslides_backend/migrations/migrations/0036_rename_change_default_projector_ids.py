from typing import Any

from datastore.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    UpdateEvent,
)
from datastore.shared.util import collection_from_fqid


class Migration(BaseEventMigration):
    """
    This migration renames default_projector_$.._id into
      default_projector_$.._ids and changes value to list.
    """

    target_migration_index = 37
    collection = "meeting"

    def modify(self, object: dict[str, Any]) -> None:
        for field in list(object.keys()):
            if field == "default_projector_$_id":
                object[field + "s"] = object[field]
                del object[field]
            elif field.startswith("default_projector_$") and field.endswith("_id"):
                object[field + "s"] = [object[field]]
                del object[field]

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection = collection_from_fqid(event.fqid)
        if collection != self.collection:
            return None

        if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
            self.modify(event.data)

        elif isinstance(event, DeleteFieldsEvent):
            for field in list(event.data):
                if field.startswith("default_projector_$") and field.endswith("_id"):
                    event.data.remove(field)
                    event.data.append(field + "s")

        elif isinstance(event, ListUpdateEvent):
            self.modify(event.add)
            self.modify(event.remove)

        return [event]
