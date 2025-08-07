from ....models.models import HistoryEntry
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("history_entry.delete", action_type=ActionType.BACKEND_INTERNAL)
class HistoryEntryDelete(DeleteAction):
    """
    Action to delete a history_entry.
    """

    model = HistoryEntry()
    schema = DefaultSchema(HistoryEntry()).get_delete_schema()
