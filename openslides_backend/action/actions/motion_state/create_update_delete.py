from typing import Any, Dict

from ....models.models import MotionState
from ....permissions.permissions import Permissions
from ....services.datastore.interface import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...action_set import ActionSet
from ...generics.update import UpdateAction
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action_set


class MotionStateCreate(CreateActionWithInferredMeeting):
    """
    Action to create motion states
    """

    relation_field_for_meeting = "workflow_id"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        if (
            first_state_of_workflow_id := instance.get("first_state_of_workflow_id")
        ) and first_state_of_workflow_id != instance["workflow_id"]:
            raise ActionException(
                f"This state of workflow {instance['workflow_id']} cannot be the first state of workflow {first_state_of_workflow_id}."
            )
        if first_state_of_workflow_id:
            workflow = self.datastore.fetch_model(
                FullQualifiedId(Collection("motion_workflow"), instance["workflow_id"]),
                ["id", "first_state_id"],
            )
            if (wf_first_state_id := workflow.get("first_state_id")) and instance[
                "id"
            ] != wf_first_state_id:
                raise ActionException(
                    "There is already a first state for this workflow set. You can't change it."
                )
        return instance


class MotionStateUpdate(UpdateAction):
    """
    Update action: check next_state_ids and previous_state_ids
    """

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check workflow_id of this state, next states and previous states.
        """
        state_ids = [instance["id"]]
        state_ids.extend(instance.get("next_state_ids", []))
        state_ids.extend(instance.get("previous_state_ids", []))

        gmr = GetManyRequest(Collection("motion_state"), state_ids, ["workflow_id"])
        db_states = self.datastore.get_many([gmr])
        states = db_states.get(Collection("motion_state"), {}).values()
        workflow_id = None
        for state in states:
            if workflow_id is None:
                workflow_id = state["workflow_id"]
            if workflow_id != state["workflow_id"]:
                raise ActionException(
                    f"Cannot update: found states from different workflows ({workflow_id}, {state['workflow_id']})"
                )

        return instance


@register_action_set("motion_state")
class MotionStateActionSet(ActionSet):
    """
    Actions to create, update and delete motion states.
    """

    model = MotionState()
    create_schema = DefaultSchema(MotionState()).get_create_schema(
        required_properties=["name", "workflow_id"],
        optional_properties=[
            "recommendation_label",
            "css_class",
            "restrictions",
            "allow_support",
            "allow_create_poll",
            "allow_submitter_edit",
            "set_number",
            "show_state_extension_field",
            "merge_amendment_into_final",
            "show_recommendation_extension_field",
            "first_state_of_workflow_id",
        ],
    )
    update_schema = DefaultSchema(MotionState()).get_update_schema(
        optional_properties=[
            "name",
            "recommendation_label",
            "css_class",
            "restrictions",
            "allow_support",
            "allow_create_poll",
            "allow_submitter_edit",
            "set_number",
            "show_state_extension_field",
            "merge_amendment_into_final",
            "show_recommendation_extension_field",
            "next_state_ids",
            "previous_state_ids",
        ]
    )
    delete_schema = DefaultSchema(MotionState()).get_delete_schema()
    permission = Permissions.Motion.CAN_MANAGE

    CreateActionClass = MotionStateCreate
    UpdateActionClass = MotionStateUpdate
