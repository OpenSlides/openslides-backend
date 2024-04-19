from typing import Any

from openslides_backend.shared.patterns import collection_from_fqid

from .. import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    UpdateEvent,
)


class RenameFieldMigration(BaseEventMigration):
    """
    This migration renames a field from old_name to new_name for one collection.
    """

    collection: str
    old_field: str
    new_field: str

    def modify(self, object: dict[str, Any]) -> None:
        if self.old_field in object:
            object[self.new_field] = object[self.old_field]
            del object[self.old_field]

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
            if self.old_field in event.data:
                event.data.remove(self.old_field)
                event.data.append(self.new_field)

        elif isinstance(event, ListUpdateEvent):
            self.modify(event.add)
            self.modify(event.remove)

        return [event]
