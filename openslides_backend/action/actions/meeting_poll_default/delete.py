from ....models.models import MeetingPollDefault
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_poll_default.delete", action_type=ActionType.BACKEND_INTERNAL)
class MeetingPollDefaultDelete(DeleteAction):
    """
    Action to delete a meeting_poll_default.
    """

    model = MeetingPollDefault()
    schema = DefaultSchema(MeetingPollDefault()).get_delete_schema()
