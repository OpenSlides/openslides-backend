from ....models.models import PollOption
from ...generics.delete_poll_collection import PollCollectionDeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll_option.delete", action_type=ActionType.BACKEND_INTERNAL)
class PollOptionDelete(PollCollectionDeleteAction):
    """
    Action to delete a poll_option.
    """

    model = PollOption()
    schema = DefaultSchema(PollOption()).get_delete_schema()
