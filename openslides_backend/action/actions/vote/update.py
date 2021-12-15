from ....models.models import Vote
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("vote.update", action_type=ActionType.BACKEND_INTERNAL)
class VoteUpdate(UpdateAction):
    """
    Internal action to update a vote.
    """

    model = Vote()
    schema = DefaultSchema(Vote()).get_update_schema(required_properties=["weight"])
