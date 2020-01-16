import os
from typing import Any, Callable, Dict, Iterable, Text, Union

from mypy_extensions import TypedDict
from werkzeug.exceptions import BadRequest, Forbidden, HTTPException
from werkzeug.routing import Map, Rule
from werkzeug.routing import RuleFactory as WerkzeugRuleFactory
from werkzeug.wrappers import Request as WerkzeugRequest
from werkzeug.wrappers import Response
from werkzeug.wrappers.json import JSONMixin  # type: ignore

from .. import logging
from ..shared.exceptions import (  # TODO: Remove PermissionDenied!!!
    PermissionDenied,
    ViewException,
)
from .environment import Environment, get_environment
from .views import view_map

logger = logging.getLogger(__name__)

ApplicationConfig = TypedDict("ApplicationConfig", {"environment": Environment})

StartResponse = Callable

WSGIEnvironment = Dict[Text, Any]


class Request(JSONMixin, WerkzeugRequest):
    """
    Customized request object. We use the JSONMixin here.
    """

    pass


class RuleFactory(WerkzeugRuleFactory):
    """
    Rule factory for the application.
    """

    def get_rules(self, map: Map) -> Iterable[Rule]:
        """
        Returns all rules that this application listens for.
        """
        return [
            Rule("/system/api/actions", endpoint="ActionView", methods=("POST",),),
        ]


class Application:
    """
    Central application container for this service.

    During initialization we bind configuration and action view to the instance
    and also map rule factory's urls.
    """

    def __init__(self, config: ApplicationConfig) -> None:
        self.environment = config["environment"]
        self.url_map = Map()
        self.url_map.add(RuleFactory())

    def dispatch_request(self, request: Request) -> Union[Response, HTTPException]:
        """
        Dispatches request to route according to URL rules. Returns a Response
        object or a HTTPException (or a subclass of it). Both are WSGI
        applications themselves.
        """
        # Find rule.
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            rule, arguments = adapter.match(return_rule=True)
        except HTTPException as exception:
            return exception
        logger.debug(f"Found rule {rule} with arguments {arguments}.")

        # Check mimetype and arse JSON body. The result is cached in request.json.
        if not request.is_json:
            return BadRequest(
                "Wrong media type. Use 'Content-Type: application/json' instead."
            )
        try:
            payload = request.get_json()
        except BadRequest as exception:
            return exception
        logger.debug(f"Request contains JSON: {payload}.")

        # Dispatch view and return response.
        view = view_map[rule.endpoint]
        try:
            view(self.environment).dispatch(payload, request.headers, **arguments)
        except ViewException as exception:
            return BadRequest(exception.message)
        except PermissionDenied as exception:
            return Forbidden(exception.message)
        return Response()

    def wsgi_application(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> Iterable[bytes]:
        """
        Creates Werkzeug's Request object, calls the dispatch_request method and
        evaluates Response object (or HTTPException) as WSGI application.
        """
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> Iterable[bytes]:
        """
        Dispatches request to `wsgi_application` method so that one may apply
        custom middlewares to the application.
        """
        return self.wsgi_application(environ, start_response)


def create_application() -> Application:
    """
    Application factory function to create a new instance of the application.

    Parses services configuration from environment variables.
    """
    # Setup global loglevel.
    if os.environ.get("OPENSLIDES_BACKEND_DEBUG"):
        logging.basicConfig(level=logging.DEBUG)

    logger.debug("Create application.")

    environment = get_environment()
    logger.debug(f"Using environment: {environment}.")

    # Create application instance.
    application = Application(ApplicationConfig(environment=environment))
    return application
