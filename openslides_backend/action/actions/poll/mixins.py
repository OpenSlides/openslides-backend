from typing import Any, Dict

from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permission, Permissions
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import KEYSEPARATOR, Collection, FullQualifiedId
from ...action import Action


class PollPermissionMixin(Action):
    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if "meeting_id" in instance:
            content_object_id = instance.get("content_object_id", "")
            meeting_id = instance["meeting_id"]
        else:
            poll = self.datastore.get(
                FullQualifiedId(Collection("poll"), instance["id"]),
                ["content_object_id", "meeting_id"],
            )
            content_object_id = poll.get("content_object_id", "")
            meeting_id = poll["meeting_id"]

        if content_object_id.startswith("motion" + KEYSEPARATOR):
            self._check_perm(Permissions.Motion.CAN_MANAGE_POLLS, meeting_id)
        elif content_object_id.startswith("assignment" + KEYSEPARATOR):
            self._check_perm(Permissions.Assignment.CAN_MANAGE, meeting_id)
        else:
            self._check_perm(Permissions.Poll.CAN_MANAGE, meeting_id)

    def _check_perm(self, perm: Permission, meeting_id: int) -> None:
        if not has_perm(self.datastore, self.user_id, perm, meeting_id):
            msg = f"You are not allowed to perform action {self.name}."
            msg += f" Missing permission: {perm}"
            raise PermissionDenied(msg)
