from typing import Any

from openslides_backend.action.action import Action
from openslides_backend.permissions.permission_helper import has_perm
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.exceptions import MissingPermission


class AgendaItemPermissionMixin(Action):
    def check_permissions(self, instance: dict[str, Any]) -> None:
        fields = set(instance.keys())
        if "id" in fields:
            fields.remove("id")
        if "moderator_notes" in fields:
            fields.remove("moderator_notes")
            perm = Permissions.AgendaItem.CAN_MANAGE_MODERATOR_NOTES
            if not has_perm(
                self.datastore,
                self.user_id,
                perm,
                self.get_meeting_id(instance),
            ):
                raise MissingPermission(perm)
        if fields:
            super().check_permissions(instance)
