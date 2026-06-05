from abc import abstractmethod
from typing import Any, Protocol

from ..shared.authenticated_service import AuthenticatedServiceInterface


class VoteService(AuthenticatedServiceInterface, Protocol):
    """
    Interface of the vote service.
    """

    @abstractmethod
    def delete(self, id: int) -> dict[str, Any]: ...
