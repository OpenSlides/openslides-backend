from typing import Any, Dict

from ...models.models import Motion
from ...shared.exceptions import ActionException
from ...shared.patterns import Collection, FullQualifiedId
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("motion.set_state")
class MotionSetStateAction(UpdateAction):
    """
    Set the state in a motion.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema(["state_id"])

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if the state_id is from a previous or next state.
        """
        motion = self.datastore.get(
            FullQualifiedId(Collection("motion"), instance["id"]), ["state_id"]
        )
        state_id = motion["state_id"]

        motion_state = self.datastore.get(
            FullQualifiedId(Collection("motion_state"), state_id),
            ["next_state_ids", "previous_state_ids"],
        )
        is_in_next_state_ids = instance["state_id"] in motion_state["next_state_ids"]
        is_in_previous_state_ids = (
            instance["state_id"] in motion_state["previous_state_ids"]
        )
        if not (is_in_next_state_ids or is_in_previous_state_ids):
            raise ActionException(
                f"State '{instance['state_id']}' is not in next or previous states of the state '{state_id}'."
            )
        return instance
