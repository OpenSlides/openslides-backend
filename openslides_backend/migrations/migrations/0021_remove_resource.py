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
    This migration removes the `resource` collection.
    """

    target_migration_index = 22

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
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
