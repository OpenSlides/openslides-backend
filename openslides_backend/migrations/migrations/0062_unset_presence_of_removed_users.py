from collections import defaultdict

from datastore.migrations import BaseModelMigration
from datastore.reader.core import GetManyRequestPart
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ...shared.filters import And, FilterOperator


class Migration(BaseModelMigration):
    """
    This migration removes the presence status if the user is not part of the meeting anymore.
    """

    target_migration_index = 63

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        present_users_per_meeting: dict[int, list[int]] = defaultdict(list)
        meetings_per_present_user: dict[int, list[int]] = defaultdict(list)

        meeting_users = self.reader.filter(
            "meeting_user",
            And(
                FilterOperator("group_ids", "=", "[]"),
                FilterOperator("meta_deleted", "!=", True),
            ),
            ["user_id", "meeting_id"],
        )
        for meeting_user in meeting_users.values():
            user_id = meeting_user["user_id"]
            meeting_id = meeting_user["meeting_id"]
            meetings_per_present_user[user_id].append(meeting_id)
            present_users_per_meeting[meeting_id].append(user_id)

        meetings = self.reader.get_many(
            [
                GetManyRequestPart(
                    "meeting",
                    [meeting_id for meeting_id in present_users_per_meeting],
                    ["present_user_ids"],
                )
            ]
        ).get("meeting", dict())
        users = self.reader.get_many(
            [
                GetManyRequestPart(
                    "user",
                    [present_user_id for present_user_id in meetings_per_present_user],
                    ["is_present_in_meeting_ids"],
                )
            ]
        ).get("user", dict())
        return [
            *[
                RequestUpdateEvent(
                    fqid_from_collection_and_id("meeting", meeting_id),
                    {
                        "present_user_ids": [
                            id_
                            for id_ in meetings.get(meeting_id, dict()).get(
                                "present_user_ids", []
                            )
                            if id_ not in user_ids
                        ]
                    },
                )
                for meeting_id, user_ids in present_users_per_meeting.items()
                if meetings
            ],
            *[
                RequestUpdateEvent(
                    fqid_from_collection_and_id("user", user_id),
                    {
                        "is_present_in_meeting_ids": [
                            id_
                            for id_ in users.get(user_id, dict()).get(
                                "is_present_in_meeting_ids", []
                            )
                            if id_ not in meeting_ids
                        ]
                    },
                )
                for user_id, meeting_ids in meetings_per_present_user.items()
            ],
        ]
