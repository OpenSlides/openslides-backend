from openslides_backend.migrations import AddFieldMigration, BaseEvent
from openslides_backend.shared.typing import JSON


class Migration(AddFieldMigration):
    """
    This migration adds `group/weight` with the id as the default weight.
    """

    target_migration_index = 18

    collection = "group"
    field = "weight"

    def get_default(self, event: BaseEvent) -> JSON:
        return event.data["id"]
