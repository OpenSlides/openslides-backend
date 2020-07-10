from typing import Any


class PermissionTestAdapter:
    """
    Test adapter for permission queries.

    See openslides_backend.adapters.protocols.PermissionProvier for
    implementation.
    """

    def __init__(self, superuser: int, *args: Any, **kwargs: Any) -> None:
        self.superuser = superuser

    def check_action(self, user_id: int, action: str, data: Any) -> bool:
        return user_id == self.superuser
