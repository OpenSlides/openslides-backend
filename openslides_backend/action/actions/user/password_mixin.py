from typing import Any, Dict

from ...action import Action


class PasswordMixin(Action):
    def set_password(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        password = instance["default_password"]
        hashed_password = self.auth.hash(password)
        instance["password"] = hashed_password
        return instance
