from typing import Any

from datastore.migrations import (
    BaseEvent,
    CreateEvent,
    ListUpdateEvent,
    RemoveFieldsMigration,
    UpdateEvent,
)
from datastore.shared.util import collection_from_fqid


class Migration(RemoveFieldsMigration):
    """
    This migration removes the field `meeting/default_projector_$user_ids`.
    """

    target_migration_index = 39
    collection_fields_map = {
        "meeting": ["default_projector_$user_ids"],
        "projector": ["used_as_default_$user_in_meeting_id"],
    }
    collection_fields_replacement_map = {
        "meeting": ["default_projector_$_ids"],
        "projector": ["used_as_default_$_in_meeting_id"],
    }

    def remove_replacement(self, obj: dict[str, Any], fields: list[str]) -> None:
        for field in fields:
            if obj.get(field) and "user" in obj[field]:
                obj[field].remove("user")
                if not obj[field]:
                    del obj[field]

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        events = super().migrate_event(event)
        if events is None:
            return events
        assert len(events) == 1
        event = events[0]
        collection = collection_from_fqid(event.fqid)
        fields = self.collection_fields_replacement_map[collection]

        if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
            self.remove_replacement(event.data, fields)
        elif isinstance(event, ListUpdateEvent):
            self.remove_replacement(event.add, fields)
            self.remove_replacement(event.remove, fields)
        return [event]
