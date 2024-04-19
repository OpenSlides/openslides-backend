from typing import Any

from openslides_backend.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    DeleteEvent,
    ListUpdateEvent,
    RestoreEvent,
)
from openslides_backend.shared.patterns import collection_and_id_from_fqid

ONE_ORGANIZATION_FQID = "organization/1"


class Migration(BaseEventMigration):
    """
    This migration adds the 1:N relation `organization/active_meeting_ids` <-> `meeting/is_active_in_organization_id`.
    This relation must be set for every meeting and link them to the one organization.

    Note that the field `organization/active_meeting_ids` is modified at the end of the migration. Why?
    Remember the single assertion about consistency within the datastore: The data is consistent *after*
    each position. When migrating single events, the consistency is not (necessarily) provided.
    One seemingly simpler but wrong migration would be:

    ```
    if isinstance(event, CreateEvent):
        event.data["is_active_in_organization_id"] = 1
        update_event = ListUpdateEvent(ONE_ORGANIZATION_FQID, {"add": {"active_meeting_ids": [id]})
        new_event = [event, update_event]
    elif isinstance(event, DeleteEvent):
        update_event = ListUpdateEvent(ONE_ORGANIZATION_FQID, {"remove": {"active_meeting_ids": [id]})
        new_event = [event, update_event]
    elif isinstance(event, RestoreEvent):
        update_event = ListUpdateEvent(ONE_ORGANIZATION_FQID, {"add": {"active_meeting_ids": [id]})
        new_event = [event, update_event]
    ```

    The problem is, that within the events of the one position it is not clear whether the organization exists!
    The organization itself might be created with the last event, so doing a ListUpdateEvent before the creation
    of the organization will fail. This is the reason `get_additional_events` is used. After migrating all events
    we can be sure, that the content is consistent (with the exception of `meeting/is_active_in_organization_id
    since we added just half of the relation). So when appending to the events we can be sure that the
    organization exists.

    Also note that The relation is not checked on the organization side since deleting (restoring, too) is
    not yet supported and since we added two new fields they are cannot be affected in any update event.
    """

    target_migration_index = 3

    def position_init(self) -> None:
        # Capture all meeting ids to add/remove from
        # `organization/active_meeting_ids` in this position.
        self.meeting_ids_to_add: set[int] = set()
        self.meeting_ids_to_remove: set[int] = set()

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection, id = collection_and_id_from_fqid(event.fqid)

        if collection != "meeting":
            return None

        if isinstance(event, CreateEvent):
            event.data["is_active_in_organization_id"] = 1
            self.meeting_ids_to_add.add(id)
            return [event]
        elif isinstance(event, DeleteEvent):
            if id in self.meeting_ids_to_add:
                self.meeting_ids_to_add.remove(id)
            else:
                self.meeting_ids_to_remove.add(id)
        elif isinstance(event, RestoreEvent):
            if id in self.meeting_ids_to_remove:
                self.meeting_ids_to_remove.remove(id)
            else:
                self.meeting_ids_to_add.add(id)
        return None

    def get_additional_events(self) -> list[BaseEvent] | None:
        if not self.meeting_ids_to_add and not self.meeting_ids_to_remove:
            return None

        payload: Any = {}
        if self.meeting_ids_to_add:
            payload["add"] = {"active_meeting_ids": list(self.meeting_ids_to_add)}
        if self.meeting_ids_to_remove:
            payload["remove"] = {"active_meeting_ids": list(self.meeting_ids_to_remove)}

        return [
            ListUpdateEvent(
                ONE_ORGANIZATION_FQID,
                payload,
            )
        ]
