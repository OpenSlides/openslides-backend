from typing import Any, Iterable, Union

from werkzeug.exceptions import BadRequest, Forbidden, HTTPException
from werkzeug.routing import Map, Rule
from werkzeug.routing import RuleFactory as WerkzeugRuleFactory
from werkzeug.wrappers import Request as WerkzeugRequest
from werkzeug.wrappers import Response
from werkzeug.wrappers.json import JSONMixin  # type: ignore

from ..shared.exceptions import (  # TODO: Remove PermissionDenied!!!
    PermissionDenied,
    ViewException,
)
from ..shared.interfaces import StartResponse, WSGIEnvironment
from .views import view_map


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


class OpenSlidesBackendApplication:
    """
    Central application class for this service.

    During initialization we bind injected dependencies to the instance and also
    map rule factory's urls.
    """

    def __init__(self, logging: Any, services: Any,) -> None:
        self.logging = logging
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialize OpenSlides Backend application.")
        self.services = services
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
        self.logger.debug(f"Found rule {rule} with arguments {arguments}.")

        # Check mimetype and arse JSON body. The result is cached in request.json.
        if not request.is_json:
            return BadRequest(
                "Wrong media type. Use 'Content-Type: application/json' instead."
            )
        try:
            payload = request.get_json()
        except BadRequest as exception:
            return exception
        self.logger.debug(f"Request contains JSON: {payload}.")

        # Dispatch view and return response.
        view_class = view_map[rule.endpoint]
        view = view_class(self.logging, self.services)
        try:
            view.dispatch(payload, request.headers, **arguments)
        except ViewException as exception:
            return BadRequest(exception.message)
        except PermissionDenied as exception:  # TODO: Do not use this here.
            return Forbidden(exception.message)
        self.logger.debug("All done. Application sends HTTP 200.")
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
