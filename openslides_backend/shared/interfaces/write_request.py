from dataclasses import dataclass, field
from typing import TypedDict, Union

from openslides_backend.shared.patterns import Field
from openslides_backend.shared.typing import JSON, HistoryInformation

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


class ListFieldsData(TypedDict, total=False):
    add: ListUpdatesDict
    remove: ListUpdatesDict


@dataclass
class BaseRequestEvent:
    fqid: str


@dataclass
class RequestCreateEvent(BaseRequestEvent):
    fields: dict[str, JSON]


@dataclass
class RequestUpdateEvent(BaseRequestEvent):
    fields: dict[str, JSON]
    list_fields: ListFieldsData

    def __post_init__(self):
        if self.list_fields is None:
            self.list_fields = {}


class RequestDeleteEvent(BaseRequestEvent):
    pass
