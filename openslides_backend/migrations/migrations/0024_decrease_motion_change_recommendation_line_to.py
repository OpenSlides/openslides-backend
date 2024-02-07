from datastore.migrations import BaseEvent, BaseEventMigration, CreateEvent
from datastore.shared.util import collection_and_id_from_fqid


class Migration(BaseEventMigration):
    """
    This migration decriments motion_change_recommendation line_to, if
    line_from < line_to.
    """

    target_migration_index = 25

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection, id = collection_and_id_from_fqid(event.fqid)

        if collection != "motion_change_recommendation":
            return None

        if isinstance(event, CreateEvent):
            if event.data["line_from"] < event.data["line_to"]:
                event.data["line_to"] -= 1
                return [event]
        return None
