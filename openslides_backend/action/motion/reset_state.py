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
        if motion.get("state_id"):
            old_state = self.database.get(
                FullQualifiedId(Collection("motion_state"), motion["state_id"]),
                ["first_state_of_workflow_id"],
            )
            if old_state.get("first_state_of_workflow_id"):
                instance["state_id"] = old_state["first_state_of_workflow_id"]
            else:
                raise ActionException("State need a first_state_of_workflow_id.")
        else:
            raise ActionException("A motion needs a state.")
        return instance
