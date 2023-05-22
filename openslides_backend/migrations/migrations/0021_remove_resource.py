from typing import List, Optional

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
    This migration removes the `resource` collection.
    """

    target_migration_index = 22

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection = collection_from_fqid(event.fqid)
        if collection == "resource":
            return []
        elif collection == "organization":
            if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
                if "resource_ids" in event.data:
                    del event.data["resource_ids"]
            elif isinstance(event, DeleteFieldsEvent):
                if "resource_ids" in event.data:
                    event.data.remove("resource_ids")
            return [event]
        return None
