from typing import Any

from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import MissingPermission
from ....shared.patterns import fqid_from_collection_and_id
from ...action import Action


class PermissionMixin(Action):
    def check_permissions(self, instance: dict[str, Any]) -> None:
        if "meeting_user_id" in instance:
            meeting_user_id = instance["meeting_user_id"]
            assignment_id = instance["assignment_id"]
        else:
            assignment_candidate = self.datastore.get(
                fqid_from_collection_and_id("assignment_candidate", instance["id"]),
                ["meeting_user_id", "assignment_id"],
                lock_result=False,
            )
            meeting_user_id = assignment_candidate.get("meeting_user_id")
            assignment_id = assignment_candidate["assignment_id"]
        assignment = self.datastore.get(
            fqid_from_collection_and_id("assignment", assignment_id),
            ["meeting_id", "phase"],
            lock_result=False,
        )
        meeting_id = assignment["meeting_id"]

        # check phase part
        if assignment.get("phase") == "voting":
            permission = Permissions.Assignment.CAN_MANAGE
            if not has_perm(self.datastore, self.user_id, permission, meeting_id):
                raise MissingPermission(permission)

        # check special assignment part
        missing_permission = None
        user = self.datastore.get(
            fqid_from_collection_and_id("user", self.user_id), ["meeting_user_ids"]
        )
        if meeting_user_id in (user.get("meeting_user_ids") or []):
            permission = Permissions.Assignment.CAN_NOMINATE_SELF
            if not has_perm(self.datastore, self.user_id, permission, meeting_id):
                missing_permission = permission
        else:
            permission = Permissions.Assignment.CAN_NOMINATE_OTHER
            if not has_perm(self.datastore, self.user_id, permission, meeting_id):
                missing_permission = permission

        if missing_permission:
            raise MissingPermission(missing_permission)
