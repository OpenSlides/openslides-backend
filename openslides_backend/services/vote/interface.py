from typing import Any, Dict, Optional, Protocol


class VoteService(Protocol):
    """
    Interface of the vote service.
    """

    def start(self, id: int) -> Dict[str, Any]:
        ...

    def stop(self, id: int) -> Dict[str, Any]:
        ...

    def clear(self, id: int) -> None:
        ...

    def clear_all(self) -> None:
        """Only for testing purposes."""

    def set_authentication(
        self, access_token: Optional[str], refresh_id: Optional[str]
    ) -> None:
        """Set the needed authentication details from the request data."""
