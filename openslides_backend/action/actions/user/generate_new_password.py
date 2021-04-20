from typing import Any, Dict

from ....models.models import User
from ....permissions.permissions import OrganisationManagementLevel
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryNoForInstanceMixin
from .password_mixin import PasswordCreateMixin
from .set_password import UserSetPasswordMixin


class UserGenerateNewPasswordMixin(UserSetPasswordMixin):
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
    CheckTemporaryNoForInstanceMixin, UserGenerateNewPasswordMixin
):
    model = User()
    schema = DefaultSchema(User()).get_update_schema()
    permission = OrganisationManagementLevel.CAN_MANAGE_USERS
