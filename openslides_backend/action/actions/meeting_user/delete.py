from typing import Any, Dict

from ....models.models import MeetingUser
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_user.delete", action_type=ActionType.STACK_INTERNAL)
class MeetingUserDeleteAction(DeleteAction):
    """
    Internal action to delete a meeting user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_delete_schema()

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
