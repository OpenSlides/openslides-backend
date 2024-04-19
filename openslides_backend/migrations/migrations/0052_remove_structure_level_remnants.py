from openslides_backend.datastore.writer.core import (
    BaseRequestEvent,
    RequestUpdateEvent,
)
from openslides_backend.migrations import BaseModelMigration
from openslides_backend.shared.patterns import fqid_from_collection_and_id


class Migration(BaseModelMigration):
    """
    This migration removes all remnants of the old structure level field in meeting users.
    """

    target_migration_index = 53

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        db_models = self.reader.get_all("meeting_user")
        for id_, model in db_models.items():
            if "structure_level" in model:
                events.append(
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("meeting_user", id_),
                        {
                            "structure_level": None,
                        },
                    )
                )
        return events
