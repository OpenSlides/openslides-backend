from time import time
from typing import Any

from ....models.models import MotionChangeRecommendation
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator, Not
from ...generics.create import CreateAction
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeetingMixin,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_change_recommendation.create")
class MotionChangeRecommendationCreateAction(
    CreateActionWithInferredMeetingMixin, CreateAction
):
    """
    Action to create motion change recommendation
    """

    model = MotionChangeRecommendation()
    schema = DefaultSchema(MotionChangeRecommendation()).get_create_schema(
        required_properties=["line_from", "line_to", "text", "motion_id"],
        optional_properties=["rejected", "internal", "type", "other_description"],
    )
    permission = Permissions.Motion.CAN_MANAGE
    history_information = "Motion change recommendation created"
    history_relation_field = "motion_id"
    relation_field_for_meeting = "motion_id"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
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
                FilterOperator("meeting_id", "=", instance["meeting_id"]),
                FilterOperator("motion_id", "=", instance["motion_id"]),
                # line_from <= line_to
                Not(FilterOperator("line_to", "<", line_from)),
                Not(FilterOperator("line_from", ">", line_to)),
            ),
        )
        if exists:
            raise ActionException(
                f"The recommendation collides with an existing one (line {line_from} - {line_to})."
            )

        instance["creation_time"] = int(time())
        return instance
