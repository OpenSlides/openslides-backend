from typing import Any

from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from ...shared.filters import And, FilterOperator


class Migration(BaseModelMigration):
    """
    This migration transfers the field values for the changed fields `meeting/default_projector_current_list_of_speakers_ids`
    and `projector/used_as_default_projector_for_current_list_of_speakers_in_meeting_id` to `meeting/default_projector_current_los_ids`
    and `projector/used_as_default_projector_for_current_los_in_meeting_id`.
    Changes the type in projections respectively and removes broken back relations from projectors.
    """

    target_migration_index = 66

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        not_deleted = FilterOperator("meta_deleted", "!=", True)
        projectors = self.reader.filter(
            "projector",
            And(
                FilterOperator(
                    "used_as_default_projector_for_current_list_of_speakers_in_meeting_id",
                    "!=",
                    None,
                ),
                not_deleted,
            ),
            ["used_as_default_projector_for_current_list_of_speakers_in_meeting_id"],
        )
        projections = self.reader.filter(
            "projection",
            And(FilterOperator("type", "=", "current_list_of_speakers"), not_deleted),
        )
        meetings = self.reader.get_all(
            "meeting", ["default_projector_current_list_of_speakers_ids"]
        )

        for id_, meeting in meetings.items():
            events.append(
                RequestUpdateEvent(
                    fqid_from_collection_and_id("meeting", id_),
                    {
                        "default_projector_current_list_of_speakers_ids": None,
                        "default_projector_current_los_ids": meeting[
                            "default_projector_current_list_of_speakers_ids"
                        ],
                    },
                )
            )

        for id_, projector in projectors.items():
            # use shortened name delivered by postgre
            meeting_id = projector[
                "used_as_default_projector_for_current_list_of_speakers_in_meeti"
            ]
            fields: dict[str, Any] = {
                "used_as_default_projector_for_current_list_of_speakers_in_meeting_id": None,
            }
            if id_ in meetings.get(meeting_id, {}).get(
                "default_projector_current_list_of_speakers_ids", []
            ):
                fields["used_as_default_projector_for_current_los_in_meeting_id"] = (
                    meeting_id
                )

            events.append(
                RequestUpdateEvent(
                    fqid_from_collection_and_id("projector", id_), fields
                )
            )

        for id_, projection in projections.items():
            events.append(
                RequestUpdateEvent(
                    fqid_from_collection_and_id("projection", id_),
                    {
                        "type": "current_los",
                    },
                )
            )
        return events
