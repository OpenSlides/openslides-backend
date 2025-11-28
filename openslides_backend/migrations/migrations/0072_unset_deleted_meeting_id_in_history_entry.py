from datastore.migrations import BaseModelMigration
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
            FilterOperator("original_model_id", "%=", "motion/%"),
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
            deleted_meetings = self.reader.filter(
                "meeting",
                And(
                    FilterOperator("meta_deleted", "=", True),
                    Or(
                        *[
                            FilterOperator("id", "=", id_)
                            for id_ in potentially_affected_meetings
                        ]
                    ),
                ),
            )
            events = [
                *[
                    RequestUpdateEvent(
                        f"history_entry/{id_}", fields={"meeting_id": None}
                    )
                    for id_, entry in potentially_broken_entries.items()
                    if entry["meeting_id"] in deleted_meetings
                ],
            ]
            # meetings = self.reader.get_many(
            #     [
            #         GetManyRequestPart("meeting", list(affected_meetings), ["meta_deleted"])
            #     ]
            # ).get("meeting", {})
            # events = [
            #     *[
            #         RequestUpdateEvent(f"history_entry/{id_}", fields={"meeting_id": None})
            #         for id_, entry in potentially_broken_entries.items()
            #         if meetings[entry["meeting_id"]].get("meta_deleted") != True
            #     ],
            # ]

        return events
