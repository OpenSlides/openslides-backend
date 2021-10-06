from typing import Any, Dict

from ....models.models import MotionState
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_state.create")
class MotionStateCreateAction(CreateActionWithInferredMeeting):
    """
    Action to create motion states
    """

    model = MotionState()
    schema = DefaultSchema(MotionState()).get_create_schema(
        required_properties=["name", "workflow_id"],
        optional_properties=[
            "weight",
            "recommendation_label",
            "css_class",
            "restrictions",
            "allow_support",
            "allow_create_poll",
            "allow_submitter_edit",
            "dont_set_identifier",
            "set_number",
            "show_state_extension_field",
            "merge_amendment_into_final",
            "show_recommendation_extension_field",
            "first_state_of_workflow_id",
        ],
    )
    permission = Permissions.Motion.CAN_MANAGE

    relation_field_for_meeting = "workflow_id"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        if (
            first_state_of_workflow_id := instance.get("first_state_of_workflow_id")
        ) and first_state_of_workflow_id != instance["workflow_id"]:
            raise ActionException(
                f"This state of workflow {instance['workflow_id']} cannot be the first state of workflow {first_state_of_workflow_id}."
            )
        workflow = self.datastore.fetch_model(
            FullQualifiedId(Collection("motion_workflow"), instance["workflow_id"]),
            ["id", "first_state_id", "meeting_id"],
        )
        if first_state_of_workflow_id:
            if (wf_first_state_id := workflow.get("first_state_id")) and instance[
                "id"
            ] != wf_first_state_id:
                raise ActionException(
                    "There is already a first state for this workflow set. You can't change it."
                )

        # set weight to max+1 if not set
        if "weight" not in instance:
            max_weight = self.datastore.max(
                Collection("motion_state"),
                And(
                    FilterOperator("meeting_id", "=", workflow["meeting_id"]),
                    FilterOperator("workflow_id", "=", workflow["id"]),
                ),
                "weight",
            )
            instance["weight"] = (max_weight or 0) + 1
        return instance
