from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent


class Migration(BaseModelMigration):
    """
    This migration enriches the database with calculated values
    for the new projector color fields "chyron_background_color_2" and "chyron_font_color_2".
    """

    target_migration_index = 64

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        db_models = self.reader.get_all("meeting", ["id"])
        for id_ in db_models.keys():
            events.append(
                RequestUpdateEvent(
                    fqid_from_collection_and_id("meeting", id_),
                    {
                        "motion_poll_projection_name_order_first": "last_name",
                        "motion_poll_projection_max_columns": 6,
                    },
                )
            )
        return events
