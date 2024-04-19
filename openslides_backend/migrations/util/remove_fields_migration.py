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


class RemoveFieldsMigration(BaseEventMigration):
    """
    This migration removes a field from all events for one collection.
    """

    collection_fields_map: dict[str, list[str]]

    def remove_fields(self, obj: dict[str, Any], fields: list[str]) -> None:
        for field in fields:
            if field in obj:
                del obj[field]

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection = collection_from_fqid(event.fqid)
        if collection not in self.collection_fields_map:
            return None
        fields = self.collection_fields_map[collection]

        if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
            self.remove_fields(event.data, fields)

        elif isinstance(event, DeleteFieldsEvent):
            for field in fields:
                if field in event.data:
                    event.data.remove(field)

        elif isinstance(event, ListUpdateEvent):
            self.remove_fields(event.add, fields)
            self.remove_fields(event.remove, fields)

        return [event]
