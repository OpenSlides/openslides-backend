from typing import Any, Dict

from openslides_backend.shared.exceptions import PermissionDenied

from ....permissions.permission_helper import is_admin
from ...action import Action


class GroupMixin(Action):
    def check_permissions(self, instance: Dict[str, Any]) -> None:
        super().check_permissions(instance)
        # external id is only allowed for admins
        if "external_id" in instance and not is_admin(
            self.datastore,
            self.user_id,
            self.get_meeting_id(instance),
        ):
            raise PermissionDenied("Missing permission: Not admin of this meeting")
