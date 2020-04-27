from .base import PresenterBase, register_presenter


@register_presenter("whoami")
class Whoami(PresenterBase):
    """Whoami represents the users identity
    """

    @property
    def data(self) -> object:
        return {
            "auth_type": "default",
            "permissions": [],
            "user_id": 1,
            "guest_enabled": True,
            "groups_id": [2],
            "short_name": "username",
        }
