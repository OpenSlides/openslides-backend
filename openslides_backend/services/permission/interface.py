from typing import Any, Dict, List, Optional, Protocol


class NotAllowed(Exception):
    def __init__(self, reason: str, error_index: Optional[int]):
        self.reason = reason
        self.error_index = error_index
        super().__init__(reason)


class PermissionService(Protocol):
    """
    Interface of the permission service.
    """

    def is_allowed(
        self, name: str, user_id: int, dataList: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Checks, if the user is allowed to execute the `name` with the list of data.
        If it is allowed, additional information will be returned for each data. If not, NotAllowed
        will be thrown providing more information.
        """
