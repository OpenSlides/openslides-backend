from ....models.models import PollEntitledUser
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll_entitled_user.delete", action_type=ActionType.BACKEND_INTERNAL)
class PollEntitledUserDelete(DeleteAction):
    """
    Action to delete a poll_entitled_user.
    """

    model = PollEntitledUser()
    schema = DefaultSchema(PollEntitledUser()).get_delete_schema()
