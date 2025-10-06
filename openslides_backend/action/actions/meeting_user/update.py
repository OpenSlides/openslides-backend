from typing import Any

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ....models.models import MeetingUser
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .history_mixin import MeetingUserHistoryMixin
from .mixin import (
    CheckLockOutPermissionMixin,
    MeetingUserGroupMixin,
    meeting_user_standard_fields,
)


@register_action("meeting_user.update", action_type=ActionType.BACKEND_INTERNAL)
class MeetingUserUpdate(
    MeetingUserHistoryMixin,
    UpdateAction,
    MeetingUserGroupMixin,
    CheckLockOutPermissionMixin,
):
    """
    Action to update a meeting_user.
    """

    merge_fields = [
        "assignment_candidate_ids",
        "motion_working_group_speaker_ids",
        "motion_editor_ids",
        "motion_supporter_ids",
        "chat_message_ids",
    ]

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_update_schema(
        optional_properties=[
            "about_me",
            "group_ids",
            *meeting_user_standard_fields,
            *merge_fields,
        ],
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        m_user = self.datastore.get(
            fqid_from_collection_and_id("meeting_user", instance["id"]),
            ["meeting_id", "user_id"],
        )
        self.check_locking_status(m_user["meeting_id"], instance, m_user["user_id"])
        return super().update_instance(instance)
