from typing import Any, Dict

from ....action.generics.update import UpdateAction
from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.mixins.user_scope_mixin import UserScopeMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .password_mixins import ClearSessionsMixin, SetPasswordMixin


@register_action("user.set_password")
class UserSetPasswordAction(
    SetPasswordMixin,
    UserScopeMixin,
    CheckForArchivedMeetingMixin,
    ClearSessionsMixin,
    UpdateAction,
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        self.set_password(instance)
        return instance
