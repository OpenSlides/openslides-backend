from abc import abstractmethod
from typing import Any, Protocol, TypedDict


class PresenterBlob(TypedDict, total=False):
    presenter: str
    data: Any
    # TODO: Check if Any is correct here.


Payload = list[PresenterBlob]
PresenterResponse = list[dict[Any, Any]]


class Presenter(Protocol):
    """
    Interface for presenter component.

    The handle_request method raises PresenterException if the request fails.
    """

    @abstractmethod
    def handle_request(self, payload: Payload, user_id: int) -> PresenterResponse: ...
