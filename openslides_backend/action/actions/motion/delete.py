from typing import Any, Dict

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PermissionHelperMixin


@register_action("motion.delete")
class MotionDelete(DeleteAction, PermissionHelperMixin):
    """
    Action to delete motions.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_delete_schema()

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
            Permissions.Motion.CAN_MANAGE,
            motion["meeting_id"],
        ):
            return

        state = self.datastore.get(
            FullQualifiedId(Collection("motion_state"), motion["state_id"]),
            ["allow_submitter_edit"],
        )
        if state.get("allow_submitter_edit") and self.is_user_submitter(
            motion["submitter_ids"]
        ):
            return

        msg = f"You are not allowed to perform action {self.name}."
        msg += f"Missing permission: {Permissions.Motion.CAN_MANAGE}"
        raise PermissionDenied(msg)
