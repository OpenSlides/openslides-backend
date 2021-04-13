import time
from typing import Any, Dict

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PermissionHelperMixin
from .set_number_mixin import SetNumberMixin


@register_action("motion.set_state")
class MotionSetStateAction(UpdateAction, SetNumberMixin, PermissionHelperMixin):
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
            FullQualifiedId(Collection("motion"), instance["id"]),
            [
                "state_id",
                "meeting_id",
                "lead_motion_id",
                "category_id",
                "number",
                "number_value",
            ],
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
        # Set number code.

        self.set_number(
            instance,
            motion["meeting_id"],
            instance["state_id"],
            motion.get("lead_motion_id"),
            motion.get("category_id"),
            motion.get("number"),
            motion.get("number_value"),
        )
        instance["last_modified"] = round(time.time())
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        motion = self.datastore.get(
            FullQualifiedId(Collection("motion"), instance["id"]),
            [
                "state_id",
                "submitter_ids",
                "meeting_id",
            ],
        )
        if has_perm(
            self.datastore,
            self.user_id,
            Permissions.Motion.CAN_MANAGE_METADATA,
            motion["meeting_id"],
        ):
            return

        if self.is_allowed_and_submitter(motion["submitter_ids"], motion["state_id"]):
            return

        msg = "You are not allowed to perform action {self.name}."
        msg += f"Missing permission: {Permissions.Motion.CAN_MANAGE_METADATA}"
        raise PermissionDenied(msg)
