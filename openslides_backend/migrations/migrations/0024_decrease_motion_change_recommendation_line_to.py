from openslides_backend.migrations import BaseEvent, BaseEventMigration, CreateEvent
from openslides_backend.shared.patterns import collection_from_fqid


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
        collection = collection_from_fqid(event.fqid)

        if collection != "motion_change_recommendation":
            return None

        if isinstance(event, CreateEvent):
            if event.data["line_from"] < event.data["line_to"]:
                event.data["line_to"] -= 1
                return [event]
        return None
