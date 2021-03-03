from typing import Any, Dict

from ....models.models import MotionState
from ....services.datastore.interface import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection
from ...action_set import ActionSet
from ...generics.update import UpdateAction
from ...mixins.create_action_with_inferred_meeting import (
    get_create_action_with_inferred_meeting,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action_set


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
            "next_state_ids",
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

    CreateActionClass = get_create_action_with_inferred_meeting("workflow_id")
    UpdateActionClass = MotionStateUpdate
