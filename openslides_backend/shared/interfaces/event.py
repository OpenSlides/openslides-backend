from enum import Enum
from typing import Any, Dict, Optional, TypedDict

from ..patterns import FullQualifiedId


class EventType(str, Enum):
    Create = "create"
    Update = "update"
    Delete = "delete"


class Event(TypedDict, total=False):
    """
    Event as part of a write request element.
    """

    type: EventType
    fields: Optional[Dict[str, Any]]
    fqid: FullQualifiedId
