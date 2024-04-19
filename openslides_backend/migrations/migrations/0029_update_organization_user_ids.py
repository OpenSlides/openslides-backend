from openslides_backend.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    DeleteEvent,
    ListUpdateEvent,
)
from openslides_backend.shared.patterns import collection_from_fqid, id_from_fqid

ONE_ORGANIZATION_ID = 1
ONE_ORGANIZATION_FQID = "organization/1"


class Migration(BaseEventMigration):
    target_migration_index = 30

    def position_init(self) -> None:
        self.user_ids: set[int] = set()

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        if collection_from_fqid(event.fqid) != "user":
            return None
        if isinstance(event, CreateEvent):
            event.data["organization_id"] = ONE_ORGANIZATION_ID
            # save the user_id to add it to the organization later, since the user create event
            # might be in order before the organization create event
            self.user_ids.add(id_from_fqid(event.fqid))
            return [event]
        elif isinstance(event, DeleteEvent):
            # a user cannot be deleted before the organization was created, so we cen return the
            # event directly
            return [
                event,
                ListUpdateEvent(
                    ONE_ORGANIZATION_FQID,
                    {"remove": {"user_ids": [id_from_fqid(event.fqid)]}},
                ),
            ]
        return None

    def get_additional_events(self) -> list[BaseEvent] | None:
        if not self.user_ids:
            return None
        return [
            ListUpdateEvent(
                ONE_ORGANIZATION_FQID, {"add": {"user_ids": list(self.user_ids)}}
            ),
        ]
