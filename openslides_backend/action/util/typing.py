from typing import Any, Dict, Iterable, List, Literal, Optional, TypedDict, Union

# the list of action data that is processed in a single action call
ActionData = Iterable[Dict[str, Any]]

# a single payload element which contains the action data for this action
PayloadElement = TypedDict("PayloadElement", {"action": str, "data": ActionData})

# the whole payload that is received from the client
Payload = List[PayloadElement | dict[str, int]]

ActionResultElement = Dict[str, Any]

ActionResults = List[Optional[ActionResultElement]]

ActionError = TypedDict(
    "ActionError",
    {"success": Literal[False], "message": str, "action_data_error_index": int},
    total=False,
)

ActionsResponseResults = List[Union[Optional[ActionResults], ActionError]]

ActionsResponse = TypedDict(
    "ActionsResponse",
    {"success": bool, "message": str, "results": ActionsResponseResults},
)
