from typing import Any, Dict

from ....models.models import MotionState
from ....permissions.permissions import Permissions
from ....services.datastore.interface import GetManyRequest
from ....shared.exceptions import ActionException
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_state.update")
class MotionStateUpdateAction(UpdateAction):
    """
    Update action: check next_state_ids and previous_state_ids
    """

    model = MotionState()
    schema = DefaultSchema(MotionState()).get_update_schema(
        optional_properties=[
            "name",
            "weight",
            "recommendation_label",
            "is_internal_recommendation",
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
            "set_workflow_timestamp",
            "allow_motion_forwarding",
            "submitter_withdraw_state_id",
        ]
    )
    permission = Permissions.Motion.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check workflow_id of this state, next states and previous states.
        """
        instance = super().update_instance(instance)

        state_ids = [instance["id"]]
        state_ids.extend(instance.get("next_state_ids", []))
        state_ids.extend(instance.get("previous_state_ids", []))

        gmr = GetManyRequest("motion_state", state_ids, ["workflow_id"])
        db_states = self.datastore.get_many([gmr])
        states = db_states.get("motion_state", {}).values()
        workflow_id = None
        for state in states:
            if workflow_id is None:
                workflow_id = state["workflow_id"]
            if workflow_id != state["workflow_id"]:
                raise ActionException(
                    f"Cannot update: found states from different workflows ({workflow_id}, {state['workflow_id']})"
                )

        return instance
