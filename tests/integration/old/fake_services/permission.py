from typing import Any, Dict, List

from openslides_backend.services.permission.interface import NotAllowed


class PermissionTestAdapter:
    """
    Test adapter for permission queries.
    See openslides_backend.adapters.protocols.PermissionProvier for
    implementation.
    """

    def __init__(self, superuser_id: int, *args: Any, **kwargs: Any) -> None:
        self.superuser_id = superuser_id

    def is_allowed(
        self, name: str, user_id: int, data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if user_id == self.superuser_id:
            return [{} for _ in data]
        else:
            raise NotAllowed("Not the superuser")
