from typing import Any, Dict, Iterable, List, Optional, TypedDict, Union

from typing_extensions import Protocol

ActionPayload = Iterable[Dict[str, Any]]

ActionPayloadWithLabel = TypedDict(
    "ActionPayloadWithLabel", {"action": str, "data": ActionPayload}
)

Payload = List[ActionPayloadWithLabel]

ActionResponseResultsElement = Dict[str, Any]

ActionResponseResults = List[Optional[List[Optional[ActionResponseResultsElement]]]]

ActionResponse = TypedDict(
    "ActionResponse",
    {"success": bool, "message": str, "results": ActionResponseResults},
)

ActionError = Any


class Action(Protocol):  # pragma: no cover
    """
    Interface for action component.
    """

    def handle_request(
        self, payload: Payload, user_id: int
    ) -> Union[ActionResponse, ActionError]:
        ...
