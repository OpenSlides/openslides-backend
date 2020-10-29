from typing import Any, Callable, Dict, Iterable, List, Optional, Text, Tuple

from mypy_extensions import TypedDict
from typing_extensions import Protocol
from werkzeug.datastructures import Headers

from .patterns import FullQualifiedId

StartResponse = Callable

WSGIEnvironment = Dict[Text, Any]


class Logger(Protocol):  # pragma: no cover
    """
    Interface for logger object provided by LoggingModule.
    """

    def debug(self, message: str) -> None:
        ...

    def info(self, message: str) -> None:
        ...

    def warning(self, message: str) -> None:
        ...

    def error(self, message: str) -> None:
        ...

    def critical(self, message: str) -> None:
        ...


class LoggingModule(Protocol):  # pragma: no cover
    """
    Interface for module to provide a hierarchical logger.
    """

    def getLogger(self, name: str) -> Logger:
        ...


class Services(Protocol):  # pragma: no cover
    """
    Interface for service container used for dependency injection.
    """

    # TODO: Use correct type here. Fitting together dependency_injector and our
    #       services seems difficult for mypy.
    authentication: Any
    permission: Any
    datastore: Any


# TODO Use proper type here: Body is ActionPayload or PresenterPayload
RequestBody = Any
ResponseBody = Optional[List[Any]]


class View(Protocol):  # pragma: no cover
    """
    Interface for views of this service.
    """

    method: str

    def __init__(self, logging: LoggingModule, services: Services) -> None:
        ...

    def dispatch(
        self, body: RequestBody, headers: Headers, cookies: Dict[str, str]
    ) -> Tuple[ResponseBody, Optional[str]]:
        ...


class WSGIApplication(Protocol):  # pragma: no cover
    """
    Interface for main WSGI application class.
    """

    def __init__(self, logging: LoggingModule, view: View, services: Services) -> None:
        ...

    def __call__(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> Iterable[bytes]:
        ...


class Permission(Protocol):  # pragma: no cover
    """
    Interface for permission service used in views and actions.
    """

    def check_action(self, user_id: int, action: str, data: Any) -> bool:
        ...

    # TODO: Add interface endpoint for readablity checks.


class Event(TypedDict, total=False):
    """
    Event as part of a write request element.
    """

    type: str
    fields: Dict[str, Any]
    fqid: FullQualifiedId


class WriteRequestElement(TypedDict):
    """
    Write request element that can be sent to the event store.
    """

    events: List[Event]
    information: Dict[FullQualifiedId, List[str]]
    user_id: int


class EventStore(Protocol):  # pragma: no cover
    """
    Interface for event store adapter used in views and actions.
    """

    def send(self, events: Iterable[WriteRequestElement]) -> None:
        ...
