from typing import Any, Dict

from ....models.models import UserMeeting
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user_meeting.delete", action_type=ActionType.STACK_INTERNAL)
class UserMeetingDeleteAction(DeleteAction):
    """
    Internal action to delete a user_meeting.
    """

    model = UserMeeting()
    schema = DefaultSchema(UserMeeting()).get_delete_schema()

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
