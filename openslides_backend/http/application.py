from typing import Any, Iterable, Union

import simplejson as json
from werkzeug.wrappers import Response

from ..services.auth.interface import AUTHENTICATION_HEADER
from ..shared.env import is_truthy
from ..shared.exceptions import ViewException
from ..shared.interfaces.wsgi import StartResponse, WSGIEnvironment
from .http_exceptions import (
    BadRequest,
    Forbidden,
    HTTPException,
    InternalServerError,
    Unauthorized,
)
from .request import Request


class OpenSlidesBackendWSGIApplication:
    """
    Central application class for this service.

    During initialization we bind injected dependencies to the instance.
    """

    def __init__(self, env: Any, logging: Any, view: Any, services: Any) -> None:
        self.env = env
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
        # Dispatch view and return response.
        view_instance = self.view(self.env, self.logging, self.services)
        try:
            response_body, access_token = view_instance.dispatch(request)
        except ViewException as exception:
            env_var = self.env.OPENSLIDES_BACKEND_RAISE_4XX
            if is_truthy(env_var):
                raise exception
            if exception.status_code == 400:
                return BadRequest(exception)
            elif exception.status_code == 401:
                return Unauthorized(exception)
            elif exception.status_code == 403:
                return Forbidden(exception)
            elif exception.status_code == 500:
                return InternalServerError(exception)
            else:
                text = (
                    f"Unknown ViewException with status_code {exception.status_code} "
                    f"raised: {exception.message}"
                )
                self.logger.error(text)
                raise
        except HTTPException as exception:
            return exception
        if isinstance(response_body, dict):
            status_code = response_body.get("status_code", 200)
        elif request.path == "/system/presenter/handle_request":
            status_code = Response.default_status
        else:
            raise ViewException(f"Unknown type of response_body:{response_body}.")

        self.logger.debug(
            f"All done. Application sends HTTP {status_code} with body {response_body}."
        )
        response = Response(
            json.dumps(response_body),
            status=status_code,
            content_type="application/json",
        )
        if access_token is not None:
            response.headers[AUTHENTICATION_HEADER] = access_token
        return response

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
