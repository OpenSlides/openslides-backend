from datastore.migrations import BaseModelMigration
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id


class Migration(BaseModelMigration):
    """
    This migration removes all moderator notes from the agenda_item.
    """

    target_migration_index = 64

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        agenda_items = self.reader.get_all(
            "agenda_item", ["id", "content_object_id", "moderator_notes"]
        )
        events: list[BaseRequestEvent] = [
            RequestUpdateEvent(
                fqid_from_collection_and_id("agenda_item", agenda_item["id"]),
                {"moderator_notes": None},
            )
            for agenda_item in agenda_items.values()
            if (agenda_item.get("moderator_notes") is not None)
        ]
        return events
