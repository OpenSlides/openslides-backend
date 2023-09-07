from typing import Any, Dict, List, Optional

from datastore.migrations import BaseModelMigration
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id


class Migration(BaseModelMigration):
    """
    Migration 44 had a typo in the field `motion/amendment_paragraph_$`. This migration fixes that.
    """

    target_migration_index = 46

    old_field = "amendment_paragraph_$"
    new_field = "amendment_paragraphs"

    def migrate_models(self) -> Optional[List[BaseRequestEvent]]:
        events: List[BaseRequestEvent] = []
        db_models = self.reader.get_all("motion")
        for id, model in db_models.items():
            if self.old_field in model:
                update: Dict[str, Any] = {self.old_field: None, self.new_field: {}}
                for replacement in model.get(self.old_field, []):
                    structured_field = self.old_field.replace("$", f"${replacement}")
                    update[structured_field] = None
                    if structured_value := model.get(structured_field):
                        update[self.new_field][replacement] = structured_value
                events.append(
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("motion", id), update
                    )
                )
        return events
