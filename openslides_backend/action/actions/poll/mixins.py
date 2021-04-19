from typing import Any, Dict

from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permission, Permissions
from ....services.datastore.interface import DatastoreService
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
        check_poll_or_option_perms(
            self.name, content_object_id, self.datastore, self.user_id, meeting_id
        )


def check_poll_or_option_perms(
    action_name: str,
    content_object_id: str,
    datastore: DatastoreService,
    user_id: int,
    meeting_id: int,
) -> None:

    if content_object_id.startswith("motion" + KEYSEPARATOR):
        _check_perm(
            datastore,
            user_id,
            Permissions.Motion.CAN_MANAGE_POLLS,
            meeting_id,
            action_name,
        )
    elif content_object_id.startswith("assignment" + KEYSEPARATOR):
        _check_perm(
            datastore,
            user_id,
            Permissions.Assignment.CAN_MANAGE,
            meeting_id,
            action_name,
        )
    else:
        _check_perm(
            datastore, user_id, Permissions.Poll.CAN_MANAGE, meeting_id, action_name
        )


def _check_perm(
    datastore: DatastoreService,
    user_id: int,
    perm: Permission,
    meeting_id: int,
    action_name: str,
) -> None:
    if not has_perm(datastore, user_id, perm, meeting_id):
        msg = f"You are not allowed to perform action {action_name}."
        msg += f" Missing permission: {perm}"
        raise PermissionDenied(msg)
