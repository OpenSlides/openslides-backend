from ....models.models import Poll
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll.set_state", action_type=ActionType.BACKEND_INTERNAL)
class PollSetState(UpdateAction):
    """
    Internal action to set state of a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema(
        required_properties=["state"],
    )
