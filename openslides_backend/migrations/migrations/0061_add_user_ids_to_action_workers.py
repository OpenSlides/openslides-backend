from datastore.migrations import BaseModelMigration
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id


class Migration(BaseModelMigration):
    """
    This migration adds the user_id "-1" to all existing action_workers.
    This is the number usually used for calls using the internal route.
    """

    target_migration_index = 62

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        action_workers = self.reader.get_all("action_worker", ["id"])
        return [
            RequestUpdateEvent(
                fqid_from_collection_and_id("action_worker", worker["id"]),
                {"user_id": -1},
            )
            for worker in action_workers.values()
        ]
