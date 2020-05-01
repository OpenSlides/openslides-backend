from typing import Any, Dict

from .base import Presenter
from .presenter import register_presenter


@register_presenter("whoami")
class Whoami(Presenter):
    """
    Whoami represents the users identity
    """

    @property
    def data(self) -> Dict[Any, Any]:
        return {
            "auth_type": "default",
            "permissions": [],
            "user_id": 1,
            "guest_enabled": True,
            "groups_id": [2],
            "short_name": "username",
        }
