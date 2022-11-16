from typing import Any, Dict

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .user_scope_permission_check_mixin import UserScopePermissionCheckMixin


class UserResetPasswordToDefaultMixin(UpdateAction, CheckForArchivedMeetingMixin):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gets the default_password and reset password.
        """
        instance = super().update_instance(instance)
        user = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["default_password"],
            lock_result=False,
        )
        default_password = self.auth.hash(str(user.get("default_password")))
        instance["password"] = default_password
        return instance


@register_action("user.reset_password_to_default")
class UserResetPasswordToDefaultAction(
    UserResetPasswordToDefaultMixin,
    UserScopePermissionCheckMixin,
):
    """
    Action to reset a password to default of a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        self.check_permissions_for_scope(instance, check_user_oml_always=True)
