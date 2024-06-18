from typing import Any

from ....shared.util import fqid_from_collection_and_id
from ...action import Action
from ...mixins.meeting_user_helper import get_groups_from_meeting_user, get_meeting_user
from .create import MeetingUserCreate


class MeetingUserHelperMixin(Action):
    def create_or_get_meeting_user(self, meeting_id: int, user_id: int) -> int:
        meeting_user = get_meeting_user(self.datastore, meeting_id, user_id, ["id"])
        if meeting_user:
            return meeting_user["id"]
        else:
            action_results = self.execute_other_action(
                MeetingUserCreate,
                [{"meeting_id": meeting_id, "user_id": user_id}],
            )
            id_ = action_results[0]["id"]  # type: ignore
            self.datastore.changed_models.get(
                fqid_from_collection_and_id("meeting_user", id_), {}
            ).pop("meta_new", None)
            return id_

    def get_meeting_user(
        self, meeting_id: int, user_id: int, fields: list[str]
    ) -> dict[str, Any] | None:
        return get_meeting_user(self.datastore, meeting_id, user_id, fields)

    def get_groups_from_meeting_user(self, meeting_id: int, user_id: int) -> list[int]:
        return get_groups_from_meeting_user(self.datastore, meeting_id, user_id)
