from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from ...shared.filters import FilterOperator


class Migration(BaseModelMigration):
    """
    This migration introduces the new gender model which enables custom gender names for non default genders.
    This requires to replace all gender strings in organization and user models to be replaced with the corresponding gender id.
    If the migration runs in memory then all gender information is left untouched since the import will still handle it as a string.
    """

    target_migration_index = 59

    def migrate_models(self) -> list[BaseRequestEvent]:
        meetings_to_fix = self.reader.filter(
            "meeting", FilterOperator("motion_poll_default_method", "=", None)
        )
        return [
            RequestUpdateEvent(
                fqid_from_collection_and_id("meeting", meeting_id),
                {"motion_poll_default_method": "YNA"},
            )
            for meeting_id, meeting in meetings_to_fix.items()
        ]
