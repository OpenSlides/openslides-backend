from typing import Any, Callable, Dict, Iterable, Optional, Text, Tuple

from typing_extensions import Protocol

from openslides_backend.http.request import Request

from . import Headers  # noqa
from .logging import LoggingModule
from .services import Services

StartResponse = Callable

WSGIEnvironment = Dict[Text, Any]


# TODO Use proper type here.
ResponseBody = Any


class View(Protocol):  # pragma: no cover
    """
    Interface for views of this service.
    """

    method: str

    def __init__(self, logging: LoggingModule, services: Services) -> None:
        ...

    def dispatch(self, request: Request) -> Tuple[ResponseBody, Optional[str]]:
        ...


class WSGIApplication(Protocol):  # pragma: no cover
    """
    Interface for main WSGI application class.
    """

    services: Services

    def __init__(self, logging: LoggingModule, view: View, services: Services) -> None:
        ...

    def __call__(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> Iterable[bytes]:
        ...
