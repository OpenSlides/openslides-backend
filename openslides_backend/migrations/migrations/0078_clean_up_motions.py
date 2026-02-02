from typing import Any

from datastore.migrations import BaseModelMigration
from datastore.writer.core.write_request import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id


class Migration(BaseModelMigration):
    """
    This migration removes the ids of non-existant or deleted meetings from motion/origin_meeting_id.
    Also removes duplicates from recommendation_extension_reference_ids.
    """

    target_migration_index = 79

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        all_existing_meeting_ids = set(self.reader.get_all("meeting", ["id"]))
        all_existing_motions = self.reader.get_all(
            "motion", ["origin_meeting_id", "recommendation_extension_reference_ids"]
        )
        events: list[BaseRequestEvent] = []
        for id_, motion in all_existing_motions.items():
            origin_meeting_id = motion.get("origin_meeting_id")
            fields: dict[str, Any] = {}
            if origin_meeting_id and origin_meeting_id not in all_existing_meeting_ids:
                fields["origin_meeting_id"] = None
            if old_rer_list := motion.get("recommendation_extension_reference_ids"):
                if len(new_rer_list := list(set(old_rer_list))) != len(old_rer_list):
                    fields["recommendation_extension_reference_ids"] = new_rer_list
            if fields:
                events.append(
                    RequestUpdateEvent(
                        fqid=fqid_from_collection_and_id("motion", id_), fields=fields
                    )
                )
        return events
