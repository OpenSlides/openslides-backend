from typing import Any, Protocol


class PermissionService(Protocol):
    """
    Interface of the permission service.
    """

    def check_action(self, user_id: int, action: str, data: Any) -> bool:
        """
        Check if the given action with the given data is allowed for the fiven user.
        """
