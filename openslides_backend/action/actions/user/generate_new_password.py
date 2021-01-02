import random
from typing import Any, Dict

from ....models.models import User
from ...action import PERMISSION_SPECIAL_CASE
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .set_password import UserSetPasswordAction


@register_action("user.generate_new_password")
class UserGenerateNewPassword(UserSetPasswordAction):

    schema = DefaultSchema(User()).get_update_schema()
    permission_description = PERMISSION_SPECIAL_CASE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates new password and call the super code.
        """
        ALLOWED_LETTERS = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "abcdefghijklmnopqrstuvwxyz" + "0123456789"
        )

        def r() -> str:
            return random.choice(ALLOWED_LETTERS)

        new_password = "".join([r() for x in range(10)])
        instance["password"] = new_password
        instance["set_as_default"] = True
        return super().update_instance(instance)
