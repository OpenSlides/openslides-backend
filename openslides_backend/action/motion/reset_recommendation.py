from typing import Any, Dict

from ...models.models import Motion
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("motion.reset_recommendation")
class MotionResetRecommendationAction(UpdateAction):
    """
    Reset motion recommendation action.
    """

    schema = DefaultSchema(Motion()).get_update_schema(properties=[])
    model = Motion()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set recommendation to None.
        """
        instance["recommendation_id"] = None
        return instance
