from typing import Any, Dict, Iterable, List, Literal, Optional, TypedDict, Union

ActionData = Iterable[Dict[str, Any]]

PayloadElement = TypedDict("PayloadElement", {"action": str, "data": ActionData})

Payload = List[PayloadElement]

ActionResultElement = Dict[str, Any]

ActionResults = List[Optional[ActionResultElement]]

ActionError = TypedDict(
    "ActionError", {"success": Literal[False], "message": str, "action_data_index": int}
)

ActionsResponseResults = List[Union[Optional[ActionResults], ActionError]]

ActionsResponse = TypedDict(
    "ActionsResponse",
    {"success": bool, "message": str, "results": ActionsResponseResults},
)
