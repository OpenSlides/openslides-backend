from abc import abstractmethod
from typing import Any, Dict, Optional, Protocol


class VoteService(Protocol):
    """
    Interface of the vote service.
    """

    @abstractmethod
    def start(self, id: int) -> None:
        ...

    @abstractmethod
    def stop(self, id: int) -> Dict[str, Any]:
        ...

    @abstractmethod
    def clear(self, id: int) -> None:
        ...

    @abstractmethod
    def clear_all(self) -> None:
        """Only for testing purposes."""

    @abstractmethod
    def set_authentication(
        self, access_token: Optional[str], refresh_id: Optional[str]
    ) -> None:
        """Set the needed authentication details from the request data."""
