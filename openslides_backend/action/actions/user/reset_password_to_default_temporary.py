from typing import Any, Dict

from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryMixin
from .reset_password_to_default import UserResetPasswordToDefaultAction


@register_action("user.reset_password_to_default_temporary")
class UserResetPasswordToDefaultTemporaryAction(
    CheckTemporaryMixin, UserResetPasswordToDefaultAction
):
    """
    Action to reset a password to default of a temporary user.
    """

    permission_description = "user.can_manage"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for temporary user and call super().update_instance().
        """
        self.check_for_temporary(instance)
        return super().update_instance(instance)
