from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent


class Migration(BaseModelMigration):
    """
    This migration adds current diff_version numbers to motions
    """

    target_migration_index = 71

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        db_models = self.reader.get_all("motion", ["id", "lead_motion_id"])
        return [
            RequestUpdateEvent(
                fqid_from_collection_and_id("motion", id_),
                {"diff_version": "0.1.2"},
            )
            for id_, motion in db_models.items()
            if not motion.get("lead_motion_id")
        ]
