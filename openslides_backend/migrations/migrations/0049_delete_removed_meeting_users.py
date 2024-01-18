from typing import List, Optional

from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestDeleteEvent


class Migration(BaseModelMigration):
    """
    This migration deletes all meeting users that don't have group_ids, as that is what the update function will do as well from now on.
    """

    target_migration_index = 50

    def migrate_models(self) -> Optional[List[BaseRequestEvent]]:
        db_models = self.reader.get_all("meeting_user")
        # to_be_deleted = [id_ for id_, meeting_user in db_models.items() if len(meeting_user.get("group_ids", [])) == 0]
        events: List[BaseRequestEvent] = [
            RequestDeleteEvent(
                fqid_from_collection_and_id("meeting_user", id_),
            )
            for id_, meeting_user in db_models.items()
            if len(meeting_user.get("group_ids", [])) == 0
        ]
        return events
