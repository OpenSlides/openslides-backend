from typing import Any, Dict, Protocol

from ...shared.interfaces import Headers


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

    def set_authentication(self, headers: Headers, cookies: Dict) -> None:
        """Set the needed authentication details from the request data."""
