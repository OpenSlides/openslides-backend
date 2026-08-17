from ....models.models import PollConfigApproval
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll_config_approval.delete", action_type=ActionType.BACKEND_INTERNAL)
class PollConfigApprovalDelete(DeleteAction):
    """
    Action to delete a poll_config_approval.
    """

    model = PollConfigApproval()
    schema = DefaultSchema(PollConfigApproval()).get_delete_schema()
