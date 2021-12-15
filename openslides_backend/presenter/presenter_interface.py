from typing import Any, Dict, List, Protocol

from mypy_extensions import TypedDict

PresenterBlob = TypedDict(
    "PresenterBlob", {"presenter": str, "data": Any}, total=False
)  # TODO: Check if Any is correct here.
Payload = List[PresenterBlob]
PresenterResponse = List[Dict[Any, Any]]


class Presenter(Protocol):  # pragma: no cover
    """
    Interface for presenter component.

    The handle_request method raises PresenterException if the request fails.
    """

    def handle_request(self, payload: Payload, user_id: int) -> PresenterResponse:
        ...
