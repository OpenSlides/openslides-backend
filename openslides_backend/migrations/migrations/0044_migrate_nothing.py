from typing import List, Optional

from datastore.migrations import (
    BaseEvent,
    BaseEventMigration,
)


class Migration(BaseEventMigration):
    """
    This migration does nothing but creating anew models collection
    """

    target_migration_index = 45

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        return [event]
