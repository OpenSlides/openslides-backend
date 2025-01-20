from dataclasses import dataclass, field
from typing import Union, TypedDict

from openslides_backend.shared.typing import JSON, HistoryInformation
from openslides_backend.shared.patterns import Field

from .collection_field_lock import CollectionFieldLock
from .event import Event


@dataclass
class WriteRequest:
    """
    Write request element that can be sent to the datastore.
    """

    events: list[Event]
    information: HistoryInformation | None = None
    user_id: int | None = None
    locked_fields: dict[str, CollectionFieldLock] = field(default_factory=dict)


@dataclass
class WriteRequestWithMigrationIndex(WriteRequest):
    """
    Write request element with a migration index.
    """

    migration_index: int | None = None


ListUpdatesDict = dict[Field, list[Union[str, int]]]


ListFieldsData = TypedDict(
    "ListFieldsData",
    {"add": ListUpdatesDict, "remove": ListUpdatesDict},
    total=False,
)


@dataclass
class BaseRequestEvent():
    fqid: str


@dataclass
class RequestCreateEvent(BaseRequestEvent):
    fields: dict[str, JSON]


@dataclass
class RequestUpdateEvent(BaseRequestEvent):
    fields: dict[str, JSON]
    list_fields: ListFieldsData = {}


class RequestDeleteEvent(BaseRequestEvent):
    pass


class RequestRestoreEvent(BaseRequestEvent):
    pass
