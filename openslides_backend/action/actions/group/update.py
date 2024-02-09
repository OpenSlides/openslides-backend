from typing import Any

from openslides_backend.shared.exceptions import PermissionDenied

from ....models.models import Group
from ....permissions.permission_helper import filter_surplus_permissions, is_admin
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .group_mixin import GroupMixin


@register_action("group.update")
class GroupUpdateAction(GroupMixin, UpdateAction):
    """
    Action to update a group.
    """

    model = Group()
    schema = DefaultSchema(Group()).get_update_schema(
        optional_properties=["external_id", "name", "permissions"]
    )
    permission = Permissions.User.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        if "permissions" in instance:
            instance["permissions"] = filter_surplus_permissions(
                instance["permissions"]
            )
        return instance

    def check_permissions(self, instance: dict[str, Any]) -> None:
        super().check_permissions(instance)
        # external id is only allowed for admins
        if "external_id" in instance and not is_admin(
            self.datastore,
            self.user_id,
            self.get_meeting_id(instance),
        ):
            raise PermissionDenied("Missing permission: Not admin of this meeting")
