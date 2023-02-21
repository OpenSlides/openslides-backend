from typing import Any, Dict, List, Optional

from datastore.migrations.core.base_migration import BaseMigration
from datastore.migrations.core.events import (
    BaseEvent,
    CreateEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    UpdateEvent,
)
from datastore.shared.util import collection_from_fqid


class Migration(BaseMigration):
    """
    This migration removes the field `meeting/default_projector_$user_ids`.
    """

    target_migration_index = 39
    collection_fields_map = {
        "meeting": ["default_projector_$user_ids"],
        "projector": ["used_as_default_$user_in_meeting_id"],
    }

    def remove_fields(self, obj: Dict[str, Any], fields: List[str]) -> None:
        for field in fields:
            if field in obj:
                del obj[field]

    def remove_replacement(self, obj: Dict[str, Any]) -> None:
        for field in ("default_projector_$_ids", "used_as_default_$_in_meeting_id"):
            if obj.get(field) and "user" in obj[field]:
                obj[field].remove("user")
                if not obj[field]:
                    del obj[field]

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection = collection_from_fqid(event.fqid)
        if collection not in self.collection_fields_map:
            return None
        fields = self.collection_fields_map[collection]

        if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
            self.remove_fields(event.data, fields)
            self.remove_replacement(event.data)

        elif isinstance(event, DeleteFieldsEvent):
            for field in fields:
                if field in event.data:
                    event.data.remove(field)

        elif isinstance(event, ListUpdateEvent):
            self.remove_fields(event.add, fields)
            self.remove_fields(event.remove, fields)
            self.remove_replacement(event.add)
            self.remove_replacement(event.remove)
        return [event]
