from ....models.models import PollConfigStvScottish
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action(
    "poll_config_stv_scottish.delete", action_type=ActionType.BACKEND_INTERNAL
)
class PollConfigStvScottishDelete(DeleteAction):
    """
    Action to delete a poll_config_stv_scottish.
    """

    model = PollConfigStvScottish()
    schema = DefaultSchema(PollConfigStvScottish()).get_delete_schema()
