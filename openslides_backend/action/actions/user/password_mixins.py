from typing import Any, Callable, Dict

from ...action import Action
from ...util.typing import ActionData


class PasswordMixin(Action):
    def set_password(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        password = instance["default_password"]
        hashed_password = self.auth.hash(password)
        instance["password"] = hashed_password
        return instance


class PasswordChangeMixin(Action):
    """Adds an on_success method to the action that clears all sessions."""

    def get_on_success(self, action_data: ActionData) -> Callable[[], None] | None:
        def on_success() -> None:
            self.auth.clear_all_sessions()

        if self.user_id > 0:
            return on_success
        else:
            return None
