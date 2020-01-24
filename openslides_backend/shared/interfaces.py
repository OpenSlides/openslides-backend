from typing import Any, Callable, Dict, Iterable, List, Text, Tuple

from mypy_extensions import TypedDict
from typing_extensions import Protocol

from ..shared.patterns import Collection, FullQualifiedField, FullQualifiedId
from .filters import Filter

LoggingModule = Any  # TODO: Use correct type here.

StartResponse = Callable

WSGIEnvironment = Dict[Text, Any]


class Services(Protocol):  # pragma: no cover
    """
    Interface for service container used for dependency injection.
    """

    # TODO: Use correct type here. Fitting together dependency_injector and our services seams difficult for mypy.
    authentication: Any
    permission: Any
    database: Any
    event_store: Any


class Application(Protocol):  # pragma: no cover
    """
    Interface for main application class.
    """

    def __init__(self, logging: LoggingModule, services: Services) -> None:
        ...

    def __call__(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> Iterable[bytes]:
        ...


class Headers(Protocol):  # pragma: no cover
    """
    Interface for headers used in authentication adapter.
    """

    def to_wsgi_list(self) -> List:
        ...


class Authentication(Protocol):  # pragma: no cover
    """
    Interface for authentication adapter used in views.
    """

    def __init__(self, authentication_url: str, logging: LoggingModule) -> None:
        ...

    def get_user(self, headers: Headers) -> int:
        ...


class Permission(Protocol):  # pragma: no cover
    """
    Interface for permission service used in views and actions.
    """

    def has_perm(self, user_id: int, permission: str) -> bool:
        ...

    def get_all(self, user_id: int) -> List[str]:
        ...


class Database(Protocol):  # pragma: no cover
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

    def exists(self, collection: Collection, ids: List[int]) -> Tuple[bool, int]:
        ...

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        meeting_id: int = None,
        mapped_fields: List[str] = None,
    ) -> Tuple[Dict[int, Dict[str, Any]], int]:
        ...

    # getAll, filter, count, min, max, ...some with deleted or only deleted


class Event(TypedDict, total=False):
    """
    Event as part of a write request element.
    """

    type: str
    fqfields: Dict[FullQualifiedField, Any]
    fqid: FullQualifiedId


class WriteRequestElement(TypedDict):
    """
    Write request element that can be sent to the event store.
    """

    events: List[Event]
    information: Dict[FullQualifiedId, List[str]]
    user_id: int
    locked_fields: Dict[Any, int]  # TODO


class EventStore(Protocol):  # pragma: no cover
    """
    Interface for event store adapter used in views and actions.
    """

    def send(self, events: Iterable[WriteRequestElement]) -> None:
        ...
