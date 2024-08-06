from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin

from ....models.models import MeetingUser
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .history_mixin import MeetingUserHistoryMixin
from .mixin import MeetingUserGroupMixin, meeting_user_standard_fields


@register_action("meeting_user.update", action_type=ActionType.BACKEND_INTERNAL)
class MeetingUserUpdate(
    MeetingUserHistoryMixin, UpdateAction, MeetingUserGroupMixin, ExtendHistoryMixin
):
    """
    Action to update a meeting_user.
    """

    merge_fields = [
        "assignment_candidate_ids",
        "motion_working_group_speaker_ids",
        "motion_editor_ids",
        "supported_motion_ids",
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
    extend_history_to = "user_id"
