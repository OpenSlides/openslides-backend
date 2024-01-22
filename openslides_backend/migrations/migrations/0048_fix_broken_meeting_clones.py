from typing import List, Optional

from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent


class Migration(BaseModelMigration):
    """
    This migration finds and fixes broken relations created by the fact that, up unil now,
    meeting.clone could create meetings that were active and archived at the same time.
    """

    target_migration_index = 49
    fields = ["set_workflow_timestamp", "allow_motion_forwarding"]

    def migrate_models(self) -> Optional[List[BaseRequestEvent]]:
        events: List[BaseRequestEvent] = []
        db_models = self.reader.get_all("meeting")
        archived_ids: List[int] = []
        active_ids: List[int] = []
        for id, model in db_models.items():
            if model.get("is_archived_in_organization_id"):
                if model.get("is_active_in_organization_id"):
                    events.append(
                        RequestUpdateEvent(
                            fqid_from_collection_and_id("meeting", id),
                            {"is_archived_in_organization_id": None},
                        )
                    )
                    active_ids.append(id)
                else:
                    archived_ids.append(id)
            else:
                active_ids.append(id)
        events.append(
            RequestUpdateEvent(
                fqid_from_collection_and_id("organization", 1),
                {
                    "active_meeting_ids": active_ids,
                    "archived_meeting_ids": archived_ids,
                },
            )
        )
        return events
