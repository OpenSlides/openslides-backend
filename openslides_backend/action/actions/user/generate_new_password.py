from typing import Any, Dict

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.mixins.user_scope_mixin import UserScopeMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .password_mixin import PasswordCreateMixin
from .set_password import UserSetPasswordMixin


class UserGenerateNewPasswordMixin(UserSetPasswordMixin, CheckForArchivedMeetingMixin):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates new password and call the super code.
        """
        new_password = PasswordCreateMixin.generate_password()
        instance["password"] = new_password
        instance["set_as_default"] = True
        return super().update_instance(instance)


@register_action("user.generate_new_password")
class UserGenerateNewPassword(
    UserGenerateNewPasswordMixin,
    UserScopeMixin,
):
    model = User()
    schema = DefaultSchema(User()).get_update_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        self.check_permissions_for_scope(instance["id"])
