from typing import Any

from openslides_backend.shared.exceptions import ActionException, PermissionDenied

from ....models.models import Group
from ....permissions.permission_helper import (
    check_if_perms_are_allowed_for_anonymous,
    filter_surplus_permissions,
    is_admin,
)
from ....permissions.permissions import Permissions
from ....services.database.commands import GetManyRequest
from ....shared.patterns import fqid_from_collection_and_id
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
        group = self.datastore.get(
            fqid_from_collection_and_id("group", instance["id"]),
            ["anonymous_group_for_meeting_id", "meeting_user_ids"],
        )
        if "permissions" in instance:
            instance["permissions"] = filter_surplus_permissions(
                instance["permissions"]
            )
            self.check_locked_users(instance, group.get("meeting_user_ids", []))
        if group.get("anonymous_group_for_meeting_id"):
            if perms := instance.get("permissions", []):
                check_if_perms_are_allowed_for_anonymous(perms)
            if "name" in instance:
                raise ActionException("Cannot change name of anonymous group.")
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

    def check_locked_users(
        self, instance: dict[str, Any], meeting_user_ids: list[int]
    ) -> None:
        if meeting_user_ids and {Permissions.User.CAN_MANAGE}.intersection(
            instance.get("permissions", [])
        ):
            meeting_users = self.datastore.get_many(
                [GetManyRequest("meeting_user", meeting_user_ids, ["locked_out"])]
            )["meeting_user"]
            if any(
                meeting_user.get("locked_out", False)
                for meeting_user in meeting_users.values()
            ):
                raise ActionException(
                    "Cannot give user manage permissions to a group with locked users."
                )
