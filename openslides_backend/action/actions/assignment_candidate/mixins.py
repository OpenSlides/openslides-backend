from typing import Any, Dict

from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action


class PermissionMixin(Action):
    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if "user_id" in instance:
            user_id = instance["user_id"]
            assignment_id = instance["assignment_id"]
        else:
            assignment_candidate = self.datastore.get(
                FullQualifiedId(Collection("assignment_candidate"), instance["id"]),
                ["user_id", "assignment_id"],
            )
            user_id = assignment_candidate["user_id"]
            assignment_id = assignment_candidate["assignment_id"]
        assignment = self.datastore.get(
            FullQualifiedId(Collection("assignment"), assignment_id),
            ["meeting_id", "phase"],
        )
        meeting_id = assignment["meeting_id"]

        missing_permissions = []
        if self.user_id == user_id:
            permission = Permissions.Assignment.CAN_NOMINATE_SELF
            if not has_perm(self.datastore, self.user_id, permission, meeting_id):
                missing_permissions.append(permission)
        else:
            permission = Permissions.Assignment.CAN_NOMINATE_OTHER
            if not has_perm(self.datastore, self.user_id, permission, meeting_id):
                missing_permissions.append(permission)
        if assignment.get("phase") == "voting":
            permission = Permissions.Assignment.CAN_MANAGE
            if not has_perm(self.datastore, self.user_id, permission, meeting_id):
                missing_permissions.append(permission)

        if missing_permissions:
            msg = f"You are not allowed to perform action {self.name}."
            msg += f" Missing permissions: {', '.join(missing_permissions)}"
            raise PermissionDenied(msg)
