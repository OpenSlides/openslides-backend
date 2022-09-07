from typing import List, Optional

from datastore.migrations import (
    BaseEvent,
    BaseMigration,
    CreateEvent,
    DeleteEvent,
    ListUpdateEvent,
)
from datastore.shared.util import collection_from_fqid, id_from_fqid

ONE_ORGANIZATION_ID = 1
ONE_ORGANIZATION_FQID = "organization/1"


class Migration(BaseMigration):

    target_migration_index = 30

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        if collection_from_fqid(event.fqid) != "user":
            return None
        if isinstance(event, CreateEvent):
            event.data["organization_id"] = ONE_ORGANIZATION_ID
            return [
                event,
                ListUpdateEvent(
                    ONE_ORGANIZATION_FQID, {"add": {"user_ids": [event.data["id"]]}}
                ),
            ]
        elif isinstance(event, DeleteEvent):
            return [
                event,
                ListUpdateEvent(
                    ONE_ORGANIZATION_FQID,
                    {"remove": {"user_ids": [id_from_fqid(event.fqid)]}},
                ),
            ]
        return None
