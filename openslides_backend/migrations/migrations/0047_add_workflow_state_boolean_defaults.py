from typing import Any, Dict, List, Optional

from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent


class Migration(BaseModelMigration):
    """
    This migration adds false boolean default to the motion_state's fields set_workflow_timestamp and allow_motion_forwarding.
    """

    target_migration_index = 48
    fields = ["set_workflow_timestamp", "allow_motion_forwarding"]

    def migrate_models(self) -> Optional[List[BaseRequestEvent]]:
        events: List[BaseRequestEvent] = []
        db_models = self.reader.get_all("motion_state")
        for id, model in db_models.items():
            update: Dict[str, Any] = {
                field: False for field in self.fields if field not in model
            }
            if len(update):
                events.append(
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("motion_state", id), update
                    )
                )
        return events
