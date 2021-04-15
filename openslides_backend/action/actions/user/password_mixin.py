import random
from typing import Any, Dict

from ....models.models import User
from ...action import BaseAction
from ...util.default_schema import DefaultSchema


class PasswordCreateMixin(BaseAction):
    """
    Action to create a user.
    """

    schema = DefaultSchema(User()).get_update_schema()

    def set_password(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        password = instance.get("default_password", "")
        instance["default_password"] = password
        hashed_password = self.auth.hash(password)
        instance["password"] = hashed_password
        return instance

    def generate_and_set_password(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        password = self.generate_password()
        instance["default_password"] = password
        hashed_password = self.auth.hash(password)
        instance["password"] = hashed_password
        return instance

    @staticmethod
    def generate_password() -> str:
        ALLOWED_LETTERS = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "abcdefghijklmnopqrstuvwxyz" + "0123456789"
        )
        return "".join(random.choice(ALLOWED_LETTERS) for i in range(10))
