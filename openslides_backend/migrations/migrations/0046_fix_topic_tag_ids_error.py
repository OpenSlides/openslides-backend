from typing import Any

from datastore.migrations import BaseModelMigration
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id


class Migration(BaseModelMigration):
    """
    Remove all topic.tag_ids from database
    """

    target_migration_index = 47

    field = "tag_ids"

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        db_models = self.reader.get_all("topic")
        for id, model in db_models.items():
            if self.field in model:
                update: dict[str, Any] = {self.field: None}
                events.append(
                    RequestUpdateEvent(fqid_from_collection_and_id("topic", id), update)
                )
        return events
