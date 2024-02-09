from typing import Any

from openslides_backend.action.mixins.check_unique_name_mixin import (
    CheckUniqueInContextMixin,
)
from openslides_backend.shared.exceptions import PermissionDenied

from ....permissions.permission_helper import is_admin
from ...action import Action


class GroupMixin(CheckUniqueInContextMixin, Action):
    def validate_instance(self, instance: dict[str, Any]) -> None:
        super().validate_instance(instance)
        if instance.get("external_id"):
            self.check_unique_in_context(
                "external_id",
                instance["external_id"],
                "The external_id of the group is not unique in the meeting scope.",
                instance.get("id"),
                "meeting_id",
                self.get_meeting_id(instance),
            )

    def check_permissions(self, instance: dict[str, Any]) -> None:
        super().check_permissions(instance)
        # external id is only allowed for admins
        if "external_id" in instance and not is_admin(
            self.datastore,
            self.user_id,
            self.get_meeting_id(instance),
        ):
            raise PermissionDenied("Missing permission: Not admin of this meeting")
