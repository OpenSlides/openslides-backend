from ....models.models import PollOption
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll_option.update", action_type=ActionType.BACKEND_INTERNAL)
class PollOptionUpdate(UpdateAction):
    """
    Action to update a poll_option.
    """

    model = PollOption()
    schema = DefaultSchema(PollOption()).get_update_schema(
        optional_properties=["content_object_id"]
    )
