from openslides_backend.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    UpdateEvent,
)
from openslides_backend.shared.patterns import collection_from_fqid


class Migration(BaseEventMigration):
    """
    This migration adds ListOfSpeakers.CAN_SEE to a group, if the ListOfSpeakers.CAN_BE_SPEAKER event is present.
    """

    target_migration_index = 42

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection = collection_from_fqid(event.fqid)
        if (
            collection == "group"
            and isinstance(event, (CreateEvent, UpdateEvent))
            and "permissions" in event.data
            and "list_of_speakers.can_be_speaker"
            in (permissions := event.data["permissions"])
            and "list_of_speakers.can_manage" not in permissions
            and "list_of_speakers.can_see" not in permissions
        ):
            permissions.append("list_of_speakers.can_see")
            return [event]
        return None
