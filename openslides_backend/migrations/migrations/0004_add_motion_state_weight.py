from openslides_backend.datastore.shared.typing import JSON
from openslides_backend.migrations import AddFieldMigration, BaseEvent


class Migration(AddFieldMigration):
    """
    This migration adds `motion_state/weight` with the id as the default weight.
    """

    target_migration_index = 5

    collection = "motion_state"
    field = "weight"

    def get_default(self, event: BaseEvent) -> JSON:
        return event.data["id"]
