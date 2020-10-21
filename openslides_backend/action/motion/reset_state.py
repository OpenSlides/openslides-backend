from typing import Any, Dict

from ...models.models import Motion
from ...shared.exceptions import ActionException
from ...shared.patterns import Collection, FullQualifiedId
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("motion.reset_state")
class MotionResetStateAction(UpdateAction):
    """
    Reset motion state action.
    """

    schema = DefaultSchema(Motion()).get_update_schema()
    model = Motion()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set state_id to motion_state.first_state_of_workflow_id.
        """
        motion = self.database.get(
            FullQualifiedId(Collection("motion"), instance["id"]), ["state_id"]
        )
        if not motion.get("state_id"):
            raise ActionException(f"Motion {instance['id']} has no state.")

        old_state = self.database.get(
            FullQualifiedId(Collection("motion_state"), motion["state_id"]),
            ["workflow_id"],
        )
        if not old_state.get("workflow_id"):
            raise ActionException(f"State {motion['state_id']} has no workflow.")

        workflow = self.database.get(
            FullQualifiedId(Collection("motion_workflow"), old_state["workflow_id"]),
            ["first_state_id"],
        )
        if not workflow.get("first_state_id"):
            raise ActionException(
                f"State {old_state['workflow_id']} has no first_state_id."
            )
        instance["state_id"] = workflow.get("first_state_id")
        return instance
