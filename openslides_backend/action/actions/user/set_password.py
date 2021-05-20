from typing import Any, Dict

from ....models.models import User
from ....permissions.management_levels import OrganisationManagementLevel
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryNoForInstanceMixin
from .user_scope_permission_check_mixin import UserScopePermissionCheckMixin


class UserSetPasswordMixin(UpdateAction):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        set hashed password and set default password if set_as_default is True.
        """
        password = instance.pop("password")
        set_as_default = False
        if "set_as_default" in instance:
            set_as_default = instance.pop("set_as_default")
        hashed_password = self.auth.hash(password)
        instance["password"] = hashed_password
        if set_as_default:
            instance["default_password"] = password
        return instance


@register_action("user.set_password")
class UserSetPasswordAction(
    CheckTemporaryNoForInstanceMixin,
    UserSetPasswordMixin,
    UserScopePermissionCheckMixin,
):
    """
    Action to set the password and default_pasword.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        required_properties=["password"],
        additional_optional_fields={"set_as_default": {"type": "boolean"}},
    )
    permission = OrganisationManagementLevel.CAN_MANAGE_USERS

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        self.check_permissions_for_scope(instance)
