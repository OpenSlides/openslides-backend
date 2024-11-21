from collections import defaultdict
from typing import Any

from datastore.migrations import BaseModelMigration
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id


class Migration(BaseModelMigration):
    """
    This migration removes the presence status if the user is not part of the meeting anymore.
    """

    target_migration_index = 63

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        present_users_per_meeting: dict[int, list[int]] = defaultdict(list)
        meetings_per_present_user: dict[int, list[int]] = defaultdict(list)
        meetings = self.reader.get_all(
            "meeting", ["group_ids", "present_user_ids", "meeting_user_ids"]
        )
        users = self.reader.get_all(
            "user", ["is_present_in_meeting_ids", "meeting_user_ids"]
        )

        def collect_removals(
            meeting_id: int,
            user_id: int,
            user: dict[str, Any],
            meetings_per_present_user: dict[int, list[int]],
            present_users_per_meeting: dict[int, list[int]],
        ) -> None:
            if not (
                (meeting_user_ids := user.get("meeting_user_ids", []))
                and any(
                    meeting_user_id in meeting_user_ids
                    for meeting_user_id in meeting.get("meeting_user_ids", [])
                )
            ):
                meetings_per_present_user[user_id].append(meeting_id)
                present_users_per_meeting[meeting_id].append(user_id)

        for meeting_id, meeting in meetings.items():
            for user_id in meeting.get("present_user_ids", []):
                user = users.get(user_id, dict())
                collect_removals(
                    meeting_id,
                    user_id,
                    user,
                    meetings_per_present_user,
                    present_users_per_meeting,
                )

        for user_id, user in users.items():
            for meeting_id in user.get("is_present_in_meeting_ids", []):
                collect_removals(
                    meeting_id,
                    user_id,
                    user,
                    meetings_per_present_user,
                    present_users_per_meeting,
                )

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
