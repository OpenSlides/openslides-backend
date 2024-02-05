import time
from typing import Any

from ....models.models import Motion
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion.reset_recommendation")
class MotionResetRecommendationAction(UpdateAction):
    """
    Reset motion recommendation action.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema()
    permission = Permissions.Motion.CAN_MANAGE_METADATA
    history_information = "Recommendation reset"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Set recommendation to None.
        """
        instance["recommendation_id"] = None
        instance["last_modified"] = round(time.time())
        return instance
