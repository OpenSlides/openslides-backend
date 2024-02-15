from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent


class Migration(BaseModelMigration):
    """
    This migration removes all default_number fields from user models
    """

    target_migration_index = 51

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        db_models = self.reader.get_all("user")
        for id_, model in db_models.items():
            if "default_number" in model:
                events.append(
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("user", id_),
                        {
                            "default_number": None,
                        },
                    )
                )
        return events
