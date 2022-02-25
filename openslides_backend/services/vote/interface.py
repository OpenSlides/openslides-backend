from typing import Any, Dict, Protocol


class VoteService(Protocol):
    """
    Interface of the vote service.
    """

    def start(self, id: int) -> None:
        ...

    def stop(self, id: int) -> Dict[str, Any]:
        ...

    def clear(self, id: int) -> None:
        ...

    def clear_all(self) -> None:
        """Only for testing purposes."""

    def set_authentication(self, access_token: str, refresh_id: str) -> None:
        """Set the needed authentication details from the request data."""
