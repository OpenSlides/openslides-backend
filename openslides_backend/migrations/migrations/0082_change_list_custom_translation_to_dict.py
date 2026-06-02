from datastore.migrations import BaseModelMigration
from datastore.writer.core.write_request import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ...shared.filters import And, FilterOperator


class Migration(BaseModelMigration):
    """
    This migration edits custom_translations with the old { original: string, translation: string }[] format
    to the current { [key: string]: string } format.
    """

    target_migration_index = 83

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        meetings = self.reader.filter(
            "meeting",
            And(
                FilterOperator("meta_deleted", "=", False),
                FilterOperator("custom_translations", "!=", None),
            ),
            ["custom_translations"],
        )
        events: list[BaseRequestEvent] = []
        for id_, data in meetings.items():
            if isinstance(
                (custom_translations := data.get("custom_translations")), list
            ):
                events.append(
                    RequestUpdateEvent(
                        fqid=fqid_from_collection_and_id("meeting", id_),
                        fields={
                            "custom_translations": {
                                transl["original"]: transl["translation"]
                                for transl in custom_translations
                            }
                        },
                    )
                )
        return events
