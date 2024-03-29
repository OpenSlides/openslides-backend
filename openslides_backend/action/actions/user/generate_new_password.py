from typing import Any

from ....action.generics.update import UpdateAction
from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permissions import Permissions
from ....shared.mixins.user_scope_mixin import UserScopeMixin
from ...util.crypto import get_random_password
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .password_mixins import ClearSessionsMixin, SetPasswordMixin


@register_action("user.generate_new_password")
class UserGenerateNewPassword(
    SetPasswordMixin,
    CheckForArchivedMeetingMixin,
    UserScopeMixin,
    ClearSessionsMixin,
    UpdateAction,
):
    model = User()
    schema = DefaultSchema(User()).get_update_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS

    def check_permissions(self, instance: dict[str, Any]) -> None:
        self.check_permissions_for_scope(
            instance["id"], meeting_permission=Permissions.User.CAN_UPDATE
        )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Generates new password and call the super code.
        """
        instance["password"] = get_random_password()
        instance["set_as_default"] = True
        self.set_password(instance)
        return instance
