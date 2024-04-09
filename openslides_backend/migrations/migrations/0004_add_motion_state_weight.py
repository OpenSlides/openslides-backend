from openslides_backend.migrations import AddFieldMigration, BaseEvent
from openslides_backend.shared.typing import JSON


class Migration(AddFieldMigration):
    """
    This migration adds `motion_state/weight` with the id as the default weight.
    """

    target_migration_index = 5

    collection = "motion_state"
    field = "weight"

    def get_default(self, event: BaseEvent) -> JSON:
        return event.data["id"]
