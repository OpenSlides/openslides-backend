from ....models.models import PollConfigSelection
from ...generics.delete_poll_collection import PollCollectionDeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action(
    "poll_config_selection.delete", action_type=ActionType.BACKEND_INTERNAL
)
class PollConfigSelectionDelete(PollCollectionDeleteAction):
    """
    Action to delete a poll_config_selection.
    """

    model = PollConfigSelection()
    schema = DefaultSchema(PollConfigSelection()).get_delete_schema()
