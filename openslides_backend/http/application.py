import os
import re
from typing import Any, Iterable, Union

import simplejson as json
from werkzeug.exceptions import BadRequest as WerkzeugBadRequest
from werkzeug.wrappers import Request as WerkzeugRequest
from werkzeug.wrappers import Response
from werkzeug.wrappers.json import JSONMixin

from ..services.auth.adapter import AUTHENTICATION_HEADER
from ..shared.exceptions import ViewException
from ..shared.interfaces.wsgi import StartResponse, WSGIEnvironment
from .http_exceptions import BadRequest, Forbidden, HTTPException, MethodNotAllowed

health_route = re.compile("^/health$")


class Request(JSONMixin, WerkzeugRequest):
    """
    Customized request object. We use the JSONMixin here.
    """

    pass


class OpenSlidesBackendWSGIApplication:
    """
    Central application class for this service.

    During initialization we bind injected dependencies to the instance.
    """

    def __init__(self, logging: Any, view: Any, services: Any) -> None:
        self.logging = logging
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialize OpenSlides Backend WSGI application.")
        self.view = view
        self.services = services

    def dispatch_request(self, request: Request) -> Union[Response, HTTPException]:
        """
        Dispatches request to route according to URL rules. Returns a Response
        object or a HTTPException (or a subclass of it). Both are WSGI
        applications themselves.
        """
        if health_route.match(request.environ["RAW_URI"]):
            return self.health_info(request)
        return self.default_route(request)

    def default_route(self, request: Request) -> Union[Response, HTTPException]:
        """
        Default route that calls the injected view.
        """
        # Check request method
        if request.method != self.view.method:
            return MethodNotAllowed(valid_methods=[self.view.method])
        self.logger.debug(f"Request method is {request.method}.")

        # Check mimetype and arse JSON body. The result is cached in request.json.
        if not request.is_json:
            return BadRequest(
                "Wrong media type. Use 'Content-Type: application/json' instead."
            )
        try:
            request_body = request.get_json()
        except WerkzeugBadRequest as exception:
            return BadRequest(exception.description)
        self.logger.debug(f"Request contains JSON: {request_body}.")

        # Dispatch view and return response.
        view_instance = self.view(self.logging, self.services)
        try:
            response_body, access_token = view_instance.dispatch(
                request_body, request.headers, request.cookies
            )
        except ViewException as exception:
            if os.environ.get("OPENSLIDES_BACKEND_RAISE_4XX"):
                raise exception
            if exception.status_code == 400:
                return BadRequest(exception.message)
            elif exception.status_code == 403:
                return Forbidden(exception.message)
            else:
                text = (
                    f"Unknown ViewException with status_code {exception.status_code} "
                    f"raised: {exception.message}"
                )
                self.logger.error(text)
                raise
        self.logger.debug(
            f"All done. Application sends HTTP 200 with body {response_body}."
        )
        response = Response(json.dumps(response_body), content_type="application/json")
        if access_token is not None:
            response.headers[AUTHENTICATION_HEADER] = access_token
        return response

    def health_info(self, request: Request) -> Union[Response, HTTPException]:
        """
        Route to provide health data of this service. Retrieves status information
        from respective view.
        """
        health_info = self.view(self.logging, self.services).get_health_info()
        return Response(
            json.dumps({"healthinfo": health_info}),
            content_type="application/json",
        )

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
