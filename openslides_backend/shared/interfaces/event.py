from enum import Enum
from typing import Any, TypedDict, Union

from typing_extensions import NotRequired

from ..patterns import FullQualifiedId


class EventType(str, Enum):
    Create = "create"
    Update = "update"
    Delete = "delete"

    def __repr__(self) -> str:
        return repr(self.value)


ListFieldsDict = dict[str, Union[list[int], list[str]]]


class ListFields(TypedDict):
    add: NotRequired[ListFieldsDict]
    remove: NotRequired[ListFieldsDict]


class Event(TypedDict):
    """
    Event as part of a write request element.
    """

    type: EventType
    fields: NotRequired[dict[str, Any]]
    list_fields: NotRequired[ListFields]
    fqid: NotRequired[FullQualifiedId]
    collection: NotRequired[str]
