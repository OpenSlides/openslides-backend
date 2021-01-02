from time import time
from typing import Any, Dict

from ....models.models import MotionChangeRecommendation
from ...action_set import ActionSet
from ...generics.create import CreateAction
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeetingMixin,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action_set


class MotionChangeRecommendationCreateAction(
    CreateActionWithInferredMeetingMixin, CreateAction
):
    """
    Action to create motion change recommendation
    """

    relation_field_for_meeting = "motion_id"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        set creation_time
        """
        instance["creation_time"] = int(time())
        return self.update_instance_with_meeting_id(instance)


@register_action_set("motion_change_recommendation")
class MotionChangeRecommendationActionSet(ActionSet):
    """
    Actions to create, update and delete motion change_recommendations.
    """

    model = MotionChangeRecommendation()
    create_schema = DefaultSchema(MotionChangeRecommendation()).get_create_schema(
        required_properties=["line_from", "line_to", "text", "motion_id"],
        optional_properties=["rejected", "internal", "type", "other_description"],
    )
    update_schema = DefaultSchema(MotionChangeRecommendation()).get_update_schema(
        optional_properties=[
            "text",
            "rejected",
            "internal",
            "type",
            "other_description",
        ]
    )
    delete_schema = DefaultSchema(MotionChangeRecommendation()).get_delete_schema()
    permission_description = "motion.can_manage"

    CreateActionClass = MotionChangeRecommendationCreateAction
