from typing import Any

from datastore.migrations import BaseModelMigration
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ...shared.filters import And, FilterOperator


class Migration(BaseModelMigration):
    """
    Migration 44 had a typo in the field `motion/amendment_paragraph_$`. This migration fixes that.
    """

    target_migration_index = 46

    old_field = "amendment_paragraph_$"
    new_field = "amendment_paragraphs"

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        db_models = self.reader.filter(
            collection="motion",
            filter=And(
                FilterOperator(self.old_field, "!=", None),
                FilterOperator("meta_deleted", "!=", True),
            ),
        )

        for id, model in db_models.items():
            update: dict[str, Any] = {self.old_field: None, self.new_field: {}}
            for replacement in model.get(self.old_field, []):
                structured_field = self.old_field.replace("$", f"${replacement}")
                update[structured_field] = None
                update[self.new_field][replacement] = model.get(structured_field)
            events.append(
                RequestUpdateEvent(fqid_from_collection_and_id("motion", id), update)
            )
        return events
