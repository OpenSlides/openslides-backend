from ....models.models import MotionSubmitter
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_submitter.update", action_type=ActionType.BACKEND_INTERNAL)
class MotionSubmitterUpdateAction(UpdateAction):
    """
    Action to update a motion_submitter's weight. Should only be called by user.merge.
    """

    model = MotionSubmitter()
    schema = DefaultSchema(MotionSubmitter()).get_update_schema(
        required_properties=[
            "weight",
        ],
    )
