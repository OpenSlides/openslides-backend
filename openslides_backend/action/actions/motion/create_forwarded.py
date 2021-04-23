from typing import Any, Dict

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create_base import MotionCreateBase


@register_action("motion.create_forwarded")
class MotionCreateForwarded(MotionCreateBase):
    """
    Create action for forwarded motions.
    """

    schema = DefaultSchema(Motion()).get_create_schema(
        optional_properties=[
            "reason",
        ],
        required_properties=["meeting_id", "title", "text", "origin_id"],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
            [
                "motions_default_workflow_id",
            ],
        )
        self.set_state_from_workflow(instance, meeting)
        self.check_for_origin_id(instance)
        self.create_submitters(instance)
        self.set_sequential_number(instance)
        self.set_created_last_modified_and_number(instance)
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        perm = Permissions.Motion.CAN_CREATE
        if not has_perm(self.datastore, self.user_id, perm, instance["meeting_id"]):
            msg = f"You are not allowed to perform action {self.name}."
            msg += f" Missing permission: {perm}"
            raise PermissionDenied(msg)

        origin = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["origin_id"]),
            ["meeting_id"],
        )
        perm_origin = Permissions.Motion.CAN_MANAGE
        if not has_perm(
            self.datastore, self.user_id, perm_origin, origin["meeting_id"]
        ):
            msg = f"You are not allowed to perform action {self.name}."
            msg += f" Missing permission: {perm_origin}"
            raise PermissionDenied(msg)
