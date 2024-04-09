from openslides_backend.datastore.shared.typing import JSON
from openslides_backend.migrations import AddFieldMigration, BaseEvent


class Migration(AddFieldMigration):
    """
    This migration adds `group/weight` with the id as the default weight.
    """

    target_migration_index = 18

    collection = "group"
    field = "weight"

    def get_default(self, event: BaseEvent) -> JSON:
        return event.data["id"]
