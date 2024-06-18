from collections.abc import Iterable
from typing import Any, Literal, Optional, TypedDict, Union

# the list of action data that is processed in a single action call
ActionData = Iterable[dict[str, Any]]


# a single payload element which contains the action data for this action
class PayloadElement(TypedDict):
    action: str
    data: ActionData


# the whole payload that is received from the client
Payload = list[PayloadElement]

ActionResultElement = dict[str, Any]

ActionResults = list[Optional[ActionResultElement]]


class ActionError(TypedDict, total=False):
    success: Literal[False]
    message: str
    action_data_error_index: int


ActionsResponseResults = list[Union[Optional[ActionResults], ActionError]]


class ActionsResponse(TypedDict):
    status_code: int | None
    success: bool
    message: str
    results: ActionsResponseResults
