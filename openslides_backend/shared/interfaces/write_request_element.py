from typing import Dict, List, TypedDict

from ..patterns import FullQualifiedId
from .event import Event


class WriteRequestElement(TypedDict):
    """
    Write request element that can be sent to the event store.
    """

    events: List[Event]
    information: Dict[FullQualifiedId, List[str]]
    user_id: int
