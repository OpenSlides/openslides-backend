from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from ...shared.filters import And, FilterOperator


class Migration(BaseModelMigration):
    """
    This migration fills the field 'motion_poll_default_method' for every meeting with 'YNA' mode if it's not set.
    This was nessecary due to being added as a default field.
    """

    target_migration_index = 59

    def migrate_models(self) -> list[BaseRequestEvent]:
        meetings_to_fix = self.reader.filter(
            "meeting",
            And(
                FilterOperator("motion_poll_default_method", "=", None),
                FilterOperator("meta_deleted", "!=", True),
            ),
        )
        return [
            RequestUpdateEvent(
                fqid_from_collection_and_id("meeting", meeting_id),
                {"motion_poll_default_method": "YNA"},
            )
            for meeting_id, meeting in meetings_to_fix.items()
        ]
