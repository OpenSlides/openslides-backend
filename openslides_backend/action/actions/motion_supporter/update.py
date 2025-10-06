from ....models.models import MotionSupporter
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_supporter.update", action_type=ActionType.BACKEND_INTERNAL)
class MotionSupporterUpdateAction(UpdateAction):
    """
    Action to update motion supporters internally (mainly for user merge).
    """

    model = MotionSupporter()
    schema = DefaultSchema(MotionSupporter()).get_update_schema(
        optional_properties=["meeting_user_id"]
    )
