from typing import Any, Dict, List, Optional, TypedDict, Union

from ..enum import Enum
from ..patterns import FullQualifiedId


class EventType(str, Enum):
    Create = "create"
    Update = "update"
    Delete = "delete"


ListFields = TypedDict(
    "ListFields",
    {
        "add": Dict[str, List[Union[int, str]]],
        "remove": Dict[str, List[Union[int, str]]],
    },
)


class Event(TypedDict, total=False):
    """
    Event as part of a write request element.
    """

    type: EventType
    fqid: FullQualifiedId
    fields: Optional[Dict[str, Any]]
    list_fields: Optional[ListFields]
