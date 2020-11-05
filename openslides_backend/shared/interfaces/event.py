from typing import Any, Dict, TypedDict

from ..patterns import FullQualifiedId


class Event(TypedDict, total=False):
    """
    Event as part of a write request element.
    """

    type: str
    fields: Dict[str, Any]
    fqid: FullQualifiedId
