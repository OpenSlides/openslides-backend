from abc import abstractmethod
from typing import Any, Protocol

from ..shared.authenticated_service import AuthenticatedServiceInterface


class VoteService(AuthenticatedServiceInterface, Protocol):
    """
    Interface of the vote service.
    """

    @abstractmethod
    def create(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def update(self, id: int, payload: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def delete(self, id: int) -> dict[str, Any]: ...

    @abstractmethod
    def start(self, id: int) -> dict[str, Any]: ...

    @abstractmethod
    def finalize(
        self, id: int, optional_attributes: list[str] = []
    ) -> dict[str, Any]: ...

    @abstractmethod
    def reset(self, id: int) -> dict[str, Any]: ...
