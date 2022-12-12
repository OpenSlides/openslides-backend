from typing import Any, Dict

from ...action import Action
from ...util.crypto import get_random_string


class PasswordCreateMixin(Action):
    def set_password(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        password = instance.get("default_password", "")
        hashed_password = self.auth.hash(password)
        instance["password"] = hashed_password
        return instance

    def generate_and_set_password(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance["default_password"] = self.generate_password()
        return self.set_password(instance)

    @staticmethod
    def generate_password() -> str:
        return get_random_string(10)
