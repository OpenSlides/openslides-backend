from datastore.migrations import BaseModelMigration
from datastore.writer.core import (
    BaseRequestEvent,
    RequestCreateEvent,
    RequestUpdateEvent,
)

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ...shared.filters import And, FilterOperator


class Migration(BaseModelMigration):
    """
    This migration replaces the supported_motion_ids-supporter_meeting_user_ids relation
    between meeting_user and motion with a new connective collection motion_supporter
    """

    target_migration_index = 71

    def migrate_models(self) -> list[BaseRequestEvent]:
        events: list[BaseRequestEvent] = []
        motions = self.reader.filter(
            "motion",
            And(
                FilterOperator("supporter_meeting_user_ids", "!=", None),
                FilterOperator("supporter_meeting_user_ids", "!=", []),
                FilterOperator("meta_deleted", "!=", True),
            ),
            ["meeting_id", "supporter_meeting_user_ids"],
        )
        next_supporter_id = 1
        for motion_id, motion in motions.items():
            motion_id = int(motion_id)
            meeting_id = motion["meeting_id"]
            supporter_ids: list[int | str] = list(
                range(
                    next_supporter_id,
                    next_supporter_id + len(motion["supporter_meeting_user_ids"]),
                )
            )
            events.extend(
                [
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("motion", motion_id),
                        {
                            "supporter_ids": supporter_ids,
                            "supporter_meeting_user_ids": None,
                        },
                    ),
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("meeting", meeting_id),
                        {},
                        {"add": {"motion_supporter_ids": supporter_ids}},
                    ),
                ]
            )
            for meeting_user_id in motion["supporter_meeting_user_ids"]:
                events.extend(
                    [
                        RequestCreateEvent(
                            fqid_from_collection_and_id(
                                "motion_supporter", next_supporter_id
                            ),
                            {
                                "id": next_supporter_id,
                                "meeting_id": meeting_id,
                                "motion_id": motion_id,
                                "meeting_user_id": meeting_user_id,
                            },
                        ),
                        RequestUpdateEvent(
                            fqid_from_collection_and_id(
                                "meeting_user", meeting_user_id
                            ),
                            {},
                            {"add": {"motion_supporter_ids": [next_supporter_id]}},
                        ),
                    ]
                )
                next_supporter_id += 1
        meeting_users = self.reader.get_all("meeting_user", ["id"])
        events.extend(
            [
                RequestUpdateEvent(
                    fqid_from_collection_and_id("meeting_user", meeting_user["id"]),
                    {"supported_motion_ids": None},
                )
                for meeting_user in meeting_users.values()
            ]
        )
        return events
