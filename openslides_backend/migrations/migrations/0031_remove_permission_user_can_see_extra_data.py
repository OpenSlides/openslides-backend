from typing import List, Optional

from datastore.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    ListUpdateEvent,
    UpdateEvent,
)
from datastore.shared.util import collection_from_fqid


class Migration(BaseEventMigration):
    """
    This migration removes the 'user.can_see_extra_data' permission from
    groups.
    """

    target_migration_index = 32
    group_permission = "user.can_see_extra_data"

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection = collection_from_fqid(event.fqid)
        if collection != "group":
            return None

        if isinstance(event, (CreateEvent, UpdateEvent)):
            if self.group_permission in event.data.get("permissions", []):
                event.data["permissions"].remove(self.group_permission)
                return [event]
        elif isinstance(event, ListUpdateEvent):
            if self.group_permission in event.add.get("permissions", []):
                event.add["permissions"].remove(self.group_permission)
            if self.group_permission in event.remove.get("permissions", []):
                event.remove["permissions"].remove(self.group_permission)
            return [event]
        return None
