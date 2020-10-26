from typing import Any, Dict

from ...models.models import Motion
from ...shared.exceptions import ActionException
from ...shared.patterns import Collection, FullQualifiedId
from ..default_schema import DefaultSchema
from ..register import register_action
from .set_state import MotionSetStateAction


@register_action("motion.follow_recommendation")
class MotionFollowRecommendationAction(MotionSetStateAction):

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        If motion has a recommendation_id, set the state to it and
        set state_extension.
        """
        motion = self.database.get(
            FullQualifiedId(Collection("motion"), instance["id"]),
            ["recommendation_id", "recommendation_extension"],
        )
        if motion.get("recommendation_id") is None:
            raise ActionException("Cannot set an empty recommendation.")
        instance["state_id"] = motion["recommendation_id"]
        instance = super().update_instance(instance)
        recommendation = self.database.get(
            FullQualifiedId(Collection("motion_state"), motion["recommendation_id"]),
            ["show_state_extension_field", "show_recommendation_extension_field"],
        )
        if (
            motion.get("recommendation_extension") is not None
            and recommendation.get("show_state_extension_field")
            and recommendation.get("show_recommendation_extension_field")
        ):
            instance["state_extension"] = motion["recommendation_extension"]
        return instance
