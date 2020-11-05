from typing import Any, Dict

from ...models.models import Motion
from ...shared.exceptions import ActionException
from ...shared.patterns import Collection, FullQualifiedId
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("motion.set_recommendation")
class MotionSetRecommendationAction(UpdateAction):
    """
    Set a recommendation in a motion.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema(["recommendation_id"])

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check recommendation workflow_id and recommendation_label.
        """
        motion = self.datastore.get(
            FullQualifiedId(Collection("motion"), instance["id"]), ["state_id"]
        )
        current_state = self.datastore.get(
            FullQualifiedId(Collection("motion_state"), motion["state_id"]),
            ["workflow_id"],
        )
        recommendation_state = self.datastore.get(
            FullQualifiedId(Collection("motion_state"), instance["recommendation_id"]),
            ["workflow_id", "recommendation_label"],
        )
        if current_state.get("workflow_id") != recommendation_state.get("workflow_id"):
            raise ActionException(
                "Cannot set recommendation. State is from a different workflow as motion."
            )
        if recommendation_state.get("recommendation_label") is None:
            raise ActionException(
                "Recommendation_label of a recommendation must be set."
            )
        return instance
