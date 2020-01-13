from typing import Any, Dict, Iterable, List, Tuple

from mypy_extensions import TypedDict
from typing_extensions import Protocol

from ..general.patterns import Collection, FullQualifiedField, FullQualifiedId
from .filters import Filter


class Headers(Protocol):  # pragma: no cover
    """
    Interface for headers used in authentication adapter.
    """

    def to_wsgi_list(self) -> List:
        ...


class AuthenticationAdapter(Protocol):  # pragma: no cover
    """
    Interface for authentication adapter used in views.
    """

    def get_user(self, headers: Headers) -> int:
        ...


class PermissionAdapter(Protocol):  # pragma: no cover
    """
    Interface for permission service used in views and actions.
    """

    def has_perm(self, user_id: int, permission: str) -> bool:
        ...


class DatabaseAdapter(Protocol):  # pragma: no cover
    """
    Interface for database adapter used in views and actions.
    """

    def get(
        self, fqid: FullQualifiedId, mapped_fields: List[str] = None
    ) -> Tuple[Dict[str, Any], int]:
        ...

    def getMany(
        self, collection: Collection, ids: List[int], mapped_fields: List[str] = None
    ) -> Tuple[Dict[int, Dict[str, Any]], int]:
        ...

    def getId(self, collection: Collection) -> Tuple[int, int]:
        ...

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        meeting_id: int = None,
        mapped_fields: List[str] = None,
    ) -> Tuple[Dict[int, Dict[str, Any]], int]:
        ...

    # def exists(self, collection: Collection, ids: List[int]) -> None: ...

    # getAll, filter, count, min, max, ...some with deleted or only deleted


class Event(TypedDict):
    """
    Event that can be sent to the event store.
    """

    type: str
    position: int
    information: Dict[str, Any]
    fields: Dict[FullQualifiedField, Any]


class EventStoreAdapter(Protocol):  # pragma: no cover
    """
    Interface for event store adapter used in views and actions.
    """

    def send(self, events: Iterable[Event]) -> None:
        ...
