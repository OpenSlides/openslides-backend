from typing import Any, Dict, List, Union

from mypy_extensions import TypedDict
from typing_extensions import Protocol

ActionPayload = Union[List[Dict[str, Any]], Dict[str, Any]]
ActionPayloadWithLabel = TypedDict(
    "ActionPayloadWithLabel", {"action": str, "data": ActionPayload}
)
Payload = List[ActionPayloadWithLabel]

ActionResult = TypedDict("ActionResult", {"success": bool, "message": str})


class Actions(Protocol):  # pragma: no cover
    """
    Interface for actions component.

    The handle_request method raises ActionException or PermissionDenied if
    the request fails.
    """

    def handle_request(self, payload: Payload, user_id: int,) -> List[ActionResult]:
        ...
