from typing import Any, Dict

from ....models.models import MeetingUser
from ....permissions.permissions import Permissions
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_user.create")
class MeetingUserCreate(CreateAction):
    """
    Action to create a meeting user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_create_schema(
        required_properties=["user_id", "meeting_id"],
        optional_properties=[
            "comment",
            "number",
            "structure_level",
            "about_me",
            "vote_weight",
            "personal_note_ids",
            "speaker_ids",
            "supported_motion_ids",
            "submitted_motion_ids",
            "assignment_candidate_ids",
            "chat_message_ids",
        ],
    )
    permission = Permissions.User.CAN_MANAGE

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if "about_me" in instance and len(instance) == 3:
            if self.user_id == instance["user_id"]:
                return
        super().check_permissions(instance)
