from abc import abstractmethod
from typing import Any, Protocol

from ..shared.authenticated_service import AuthenticatedServiceInterface


class VoteService(AuthenticatedServiceInterface, Protocol):
    """
    Interface of the vote service.
    """

    @abstractmethod
    def start(self, id: int) -> dict[str, Any]:
        ...

    @abstractmethod
    def stop(self, id: int) -> dict[str, Any]: ...

    @abstractmethod
    def clear(self, id: int) -> None: ...

    @abstractmethod
    def clear_all(self) -> None:
        """Only for testing purposes."""
