from typing import Any, Dict

from ..register import register_action
from .check_temporary_mixin import CheckTemporaryMixin
from .set_password import UserSetPasswordAction


@register_action("user.set_password_temporary")
class UserSetPasswordTemporaryAction(CheckTemporaryMixin, UserSetPasswordAction):
    """
    Action to set the password of a temporary user.
    """

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a user is a temporary user.
        """
        self.check_for_temporary(instance)
        return super().update_instance(instance)
