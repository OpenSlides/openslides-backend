from typing import Any, Dict, List

from mypy_extensions import TypedDict
from typing_extensions import Protocol

PresenterBlob = TypedDict("PresenterBlob", {"presenter": str, "data": Any})
Payload = List[PresenterBlob]
PresenterResponse = List[Dict[Any, Any]]


class Presenter(Protocol):  # pragma: no cover
    """
    Interface for presenter component.

    The handle_request method raises PresenterException if the request fails.
    """

    def handle_request(self, payload: Payload, user_id: int) -> PresenterResponse:
        ...
