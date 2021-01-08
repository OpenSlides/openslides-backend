from typing import Any, Dict, List, Protocol


class PermissionService(Protocol):
    """
    Interface of the permission service.
    """

    def is_allowed(
        self, name: str, user_id: int, data_list: List[Dict[str, Any]]
    ) -> bool:
        ...
