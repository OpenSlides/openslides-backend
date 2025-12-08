from ....models.models import HistoryPosition
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("history_position.delete", action_type=ActionType.BACKEND_INTERNAL)
class HistoryPositionDelete(DeleteAction):
    """
    Action to delete a history_position.
    """

    model = HistoryPosition()
    schema = DefaultSchema(HistoryPosition()).get_delete_schema()
