from typing import Any, Dict

from ....models.models import User
from ....permissions.management_levels import OrganisationManagementLevel
from ....shared.patterns import FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryNoForInstanceMixin


class UserResetPasswordToDefaultMixin(UpdateAction):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gets the default_password and reset password.
        """
        instance = super().update_instance(instance)
        user = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]), ["default_password"]
        )
        default_password = self.auth.hash(str(user.get("default_password")))
        instance["password"] = default_password
        return instance


@register_action("user.reset_password_to_default")
class UserResetPasswordToDefaultAction(
    CheckTemporaryNoForInstanceMixin, UserResetPasswordToDefaultMixin
):
    """
    Action to reset a password to default of a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema()
    permission = OrganisationManagementLevel.CAN_MANAGE_USERS
