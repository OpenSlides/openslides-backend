from abc import abstractmethod
from typing import Any, Callable, Dict, Iterable, Optional, Protocol, Text, Tuple

from openslides_backend.http.request import Request
from openslides_backend.shared.env import Environment

from . import Headers  # noqa
from .logging import LoggingModule
from .services import Services

StartResponse = Callable

WSGIEnvironment = Dict[Text, Any]


# TODO Use proper type here.
ResponseBody = Any


class View(Protocol):
    """
    Interface for views of this service.
    """

    @abstractmethod
    def __init__(self, logging: LoggingModule, services: Services) -> None: ...

    @abstractmethod
    def dispatch(self, request: Request) -> Tuple[ResponseBody, Optional[str]]: ...


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
