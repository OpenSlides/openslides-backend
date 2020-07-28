from typing import Any, Dict

from .base import BasePresenter
from .presenter import register_presenter


@register_presenter("whoami")
class Whoami(BasePresenter):
    """
    Whoami represents the users identity
    """

    def get_result(self) -> Any:
        return {
            "auth_type": "default",
            "permissions": [],
            "user_id": 1,
            "guest_enabled": True,
            "groups_id": [2],
            "short_name": "username",
        }
