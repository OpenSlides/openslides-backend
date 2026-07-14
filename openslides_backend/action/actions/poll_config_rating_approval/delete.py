from ....models.models import PollConfigRatingApproval
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action(
    "poll_config_rating_approval.delete", action_type=ActionType.BACKEND_INTERNAL
)
class PollConfigRatingApprovalDelete(DeleteAction):
    """
    Action to delete a poll_config_rating_approval.
    """

    model = PollConfigRatingApproval()
    schema = DefaultSchema(PollConfigRatingApproval()).get_delete_schema()
