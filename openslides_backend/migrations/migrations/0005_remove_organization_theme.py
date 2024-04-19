from openslides_backend.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    DeleteFieldsEvent,
    UpdateEvent,
)
from openslides_backend.shared.patterns import collection_from_fqid


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
    ) -> list[BaseEvent] | None:
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
