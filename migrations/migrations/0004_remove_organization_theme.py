from typing import Any, Dict, List, Optional

from datastore.migrations.core.base_migration import BaseMigration
from datastore.migrations.core.events import BaseEvent, CreateEvent, UpdateEvent
from datastore.shared.util import collection_from_fqid


class Migration(BaseMigration):
    """
    This migration removes `organization/theme`.
    """

    target_migration_index = 5

    collection: str = "organization"
    field: str = "theme"

    def modify(self, obj: Dict[str, Any]) -> None:
        if self.field in obj:
            del obj[self.field]

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection = collection_from_fqid(event.fqid)
        if collection != self.collection:
            return None

        if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
            self.modify(event.data)

        return [event]
