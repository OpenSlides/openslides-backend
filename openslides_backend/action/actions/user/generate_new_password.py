import random
from typing import Any, Dict

from ....models.models import User
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .set_password import UserSetPasswordAction
from .password_mixin import PasswordCreateMixin

@register_action("user.generate_new_password")
class UserGenerateNewPassword(UserSetPasswordAction):

    schema = DefaultSchema(User()).get_update_schema()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates new password and call the super code.
        """
        new_password = PasswordCreateMixin.generate_password()
        instance["password"] = new_password
        instance["set_as_default"] = True
        return super().update_instance(instance)
