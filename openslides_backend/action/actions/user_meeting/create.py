from typing import Any, Dict

from ....models.models import UserMeeting
from ...generics.create import CreateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user_meeting.create", action_type=ActionType.STACK_INTERNAL)
class UserMeetingCreateAction(CreateAction):
    """
    Internal action to create a user meeting.
    """

    model = UserMeeting()
    schema = DefaultSchema(UserMeeting()).get_create_schema(
        required_properties=["user_id", "meeting_id"],
        optional_properties=[],  # TODO add moved fields here
    )

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
