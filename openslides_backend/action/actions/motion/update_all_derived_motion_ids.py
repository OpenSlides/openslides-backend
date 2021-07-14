from ....models.models import Motion
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion.update_all_derived_motion_ids", internal=True)
class MotionUpdateAllDerivedMotionIds(UpdateAction):
    """
    Action to update the all_derived_motion_ids of a motion.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema(
        required_properties=["all_derived_motion_ids"]
    )
