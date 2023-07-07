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
    This migration does nothing but creating anew models collection
    """

    target_migration_index = 45

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        return [event]
