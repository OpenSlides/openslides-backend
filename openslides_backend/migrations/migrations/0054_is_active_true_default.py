from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from ...shared.filters import FilterOperator


class Migration(BaseModelMigration):
    """
    This migration writes True into every user/is_active field that is currently not set at all
    """

    target_migration_index = 55

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        users = self.reader.filter(
            "user",
            FilterOperator("is_active", "=", None),
            [],
        )
        events: list[BaseRequestEvent] = [
            RequestUpdateEvent(
                fqid_from_collection_and_id("user", id_), {"is_active": True}
            )
            for id_ in users
        ]
        return events
