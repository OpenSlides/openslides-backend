from typing import Any, Dict

from ....models.models import UserMeeting
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user_meeting.update", action_type=ActionType.STACK_INTERNAL)
class UserMeetingUpdateAction(UpdateAction):
    """
    Internal action to update a user_meeting.
    """

    model = UserMeeting()
    schema = DefaultSchema(UserMeeting()).get_update_schema(
        optional_properties=[
            "meeting_id",
            "user_id",
            # TODO: add moved fields here.
        ],
    )

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
