from typing import Any, Dict

from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryMixin
from .generate_new_password import UserGenerateNewPassword


@register_action("user.generate_new_password_temporary")
class UserGenerateNewPasswordTemporaryAction(
    CheckTemporaryMixin, UserGenerateNewPassword
):
    permission_description = "user.can_manage"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for temporary user and calls the super code.
        """
        self.check_for_temporary(instance)
        return super().update_instance(instance)
