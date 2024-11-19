from collections import defaultdict

from datastore.migrations import BaseModelMigration
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id


class Migration(BaseModelMigration):
    """
    This migration adds the user_id "-1" to all existing action_workers.
    This is the number usually used for calls using the internal route.
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

        def helper() -> None:
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
                helper()

        for user_id, user in users.items():
            for meeting_id in user.get("is_present_in_meeting_ids", []):
                helper()

        return [
            RequestUpdateEvent(
                fqid_from_collection_and_id(what_collection, what_id),
                {
                    field: [
                        id_
                        for id_ in lookup.get(what_id, dict()).get(field, [])
                        if id_ not in which_ids
                    ]
                },
            )
            for lookup, cross_lookup, what_collection, field in [
                (meetings, present_users_per_meeting, "meeting", "present_user_ids"),
                (users, meetings_per_present_user, "user", "is_present_in_meeting_ids"),
            ]
            for what_id, which_ids in cross_lookup.items()
        ]
