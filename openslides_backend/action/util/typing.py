from typing import Any, Dict, Iterable, List, Optional, TypedDict

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
