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
    This migration removes `organization/theme`.
    """

    target_migration_index = 6

    collection: str = "organization"
    field: str = "theme"

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection = collection_from_fqid(event.fqid)
        if collection != self.collection:
            return None

        if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
            if self.field in event.data:
                del event.data[self.field]
        elif isinstance(event, DeleteFieldsEvent):
            if self.field in event.data:
                event.data.remove(self.field)

        return [event]
