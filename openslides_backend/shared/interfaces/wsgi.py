from abc import abstractmethod
from collections.abc import Callable, Iterable
from typing import Any, Protocol

from openslides_backend.http.request import Request
from openslides_backend.shared.env import Environment

from . import Headers  # noqa
from .logging import LoggingModule
from .services import Services

StartResponse = Callable

WSGIEnvironment = dict[str, Any]


# TODO Use proper type here.
ResponseBody = Any

RouteResponse = tuple[ResponseBody, str | None]


class View(Protocol):
    """
    Interface for views of this service.
    """

    @abstractmethod
    def __init__(self, logging: LoggingModule, services: Services) -> None: ...

    @abstractmethod
    def dispatch(self, request: Request) -> RouteResponse: ...


class WSGIApplication(Protocol):
    """
    Interface for main WSGI application class.
    """

    services: Services
    env: Environment

    @abstractmethod
    def __init__(
        self, logging: LoggingModule, view: View, services: Services
    ) -> None: ...

    @abstractmethod
    def __call__(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> Iterable[bytes]: ...
