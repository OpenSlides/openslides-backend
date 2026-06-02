from enum import StrEnum
from typing import Any, TypedDict

from typing_extensions import NotRequired

from ..patterns import FullQualifiedId


class EventType(StrEnum):
    Create = "create"
    Update = "update"
    Delete = "delete"

    def __repr__(self) -> str:
        return repr(self.value)


ListField = list[int] | list[str]
ListFieldsDict = dict[str, ListField]


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
    return_fields: NotRequired[list[str]]
