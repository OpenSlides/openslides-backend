from ....models.models import MeetingUser
from ....permissions.permissions import Permissions
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_user.delete")
class MeetingUserDelete(DeleteAction):
    """
    Action to delete a meeting user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_delete_schema()
    permission = Permissions.User.CAN_MANAGE
