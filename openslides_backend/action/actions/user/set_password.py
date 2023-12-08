from typing import Any, Dict

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.mixins.user_scope_mixin import UserScopeMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .password_mixins import PasswordChangeMixin, UserSetPasswordMixin


@register_action("user.set_password")
class UserSetPasswordAction(
    UserSetPasswordMixin,
    UserScopeMixin,
    CheckForArchivedMeetingMixin,
    PasswordChangeMixin,
):
    """
    Action to set the password and default_pasword.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        required_properties=["password"],
        additional_optional_fields={"set_as_default": {"type": "boolean"}},
    )
    history_information = "Password changed"
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        self.check_permissions_for_scope(instance["id"])
