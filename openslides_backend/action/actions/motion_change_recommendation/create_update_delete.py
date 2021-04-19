from time import time
from typing import Any, Dict

from ....models.models import MotionChangeRecommendation
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator, Not
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
        Check for colliding change recommendations and set creation time.
        """
        line_from = instance["line_from"]
        line_to = instance["line_to"]
        if line_from > line_to:
            raise ActionException("Starting line must be smaller than ending line.")

        instance = self.update_instance_with_meeting_id(instance)
        exists = self.datastore.exists(
            self.model.collection,
            And(
                # adding meeting id for improved query speed
                FilterOperator("meeting_id", "=", instance["meeting_id"]),
                FilterOperator("motion_id", "=", instance["motion_id"]),
                Not(
                    And(
                        FilterOperator("line_from", "<", line_from),
                        FilterOperator("line_to", "<=", line_from),
                    )
                ),
                Not(
                    And(
                        FilterOperator("line_from", ">=", line_to),
                        FilterOperator("line_to", ">", line_to),
                    )
                ),
            ),
            lock_result=True,
        )
        if exists:
            raise ActionException(
                f"The recommendation collides with an existing one (line {line_from} - {line_to})."
            )

        instance["creation_time"] = int(time())
        return instance


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

    CreateActionClass = MotionChangeRecommendationCreateAction
