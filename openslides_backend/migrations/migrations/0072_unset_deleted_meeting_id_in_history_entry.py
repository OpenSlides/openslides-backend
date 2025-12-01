from datastore.migrations import BaseModelMigration
from datastore.reader.core.requests import GetManyRequestPart
from datastore.writer.core.write_request import BaseRequestEvent, RequestUpdateEvent

from ...shared.filters import And, FilterOperator, Or


class Migration(BaseModelMigration):
    """
    This migration removes mistakenly created history collection entries
    """

    target_migration_index = 73

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        if self.reader.is_in_memory_migration:
            return None
        events: list[BaseRequestEvent] = []
        filter_ = And(
            Or(
                FilterOperator("original_model_id", "%=", f"{collection}/%")
                for collection in ["assignment", "motion", "user"]
            ),
            FilterOperator("meeting_id", "!=", None),
            FilterOperator("meta_deleted", "!=", True),
        )
        potentially_broken_entries = self.reader.filter(
            "history_entry", filter_, ["meeting_id"]
        )
        potentially_affected_meetings = {
            meeting_id
            for entry in potentially_broken_entries.values()
            if (meeting_id := entry.get("meeting_id"))
        }
        if potentially_broken_entries:
            meetings = self.reader.get_many(
                [
                    GetManyRequestPart(
                        "meeting", list(potentially_affected_meetings), ["meta_deleted"]
                    )
                ]
            ).get("meeting", {})
            events = [
                *[
                    RequestUpdateEvent(
                        f"history_entry/{id_}", fields={"meeting_id": None}
                    )
                    for id_, entry in potentially_broken_entries.items()
                    if entry["meeting_id"] not in meetings
                ],
            ]

        return events
