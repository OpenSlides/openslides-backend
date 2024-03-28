from collections.abc import Iterable
from pathlib import Path

import simplejson as json
from werkzeug.wrappers import Response

from openslides_backend.action.action_handler import ActionHandler
from openslides_backend.http.views.action_view import ActionView
from openslides_backend.http.views.base_view import BaseView
from openslides_backend.shared.interfaces.env import Env
from openslides_backend.shared.interfaces.logging import LoggingModule
from openslides_backend.shared.interfaces.services import Services

from ..services.auth.interface import AUTHENTICATION_HEADER
from ..shared.env import is_truthy
from ..shared.exceptions import ActionException, ViewException
from ..shared.interfaces.wsgi import StartResponse, WSGIApplication, WSGIEnvironment
from .http_exceptions import (
    BadRequest,
    Forbidden,
    HTTPException,
    InternalServerError,
    Unauthorized,
)
from .request import Request


class OpenSlidesBackendWSGIApplication(WSGIApplication):
    """
    Central application class for this service.

    During initialization we bind injected dependencies to the instance.
    """

    def __init__(
        self,
        env: Env,
        logging: LoggingModule,
        view: type[BaseView],
        services: Services,
    ) -> None:
        self.env = env
        self.logging = logging
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialize OpenSlides Backend WSGI application.")
        self.view = view
        self.services = services
        if issubclass(view, ActionView):
            self.create_initial_data()

    def create_initial_data(self) -> None:
        if is_truthy(self.env.OPENSLIDES_BACKEND_CREATE_INITIAL_DATA):
            self.logger.info("Creating initial data...")
            # use example data in dev mode and initial data in prod mode
            file_prefix = "example" if self.env.is_dev_mode() else "initial"
            initial_data_path = (
                Path(__file__).parent
                / ".."
                / ".."
                / "global"
                / "data"
                / f"{file_prefix}-data.json"
            )
            with open(initial_data_path) as file:
                initial_data = json.load(file)
            handler = ActionHandler(self.env, self.services, self.logging)
            try:
                handler.execute_internal_action(
                    "organization.initial_import",
                    {"data": initial_data},
                )
            except ActionException as e:
                self.logger.error(f"Initial data creation failed: {e}")

            # in prod mode, set superadmin password
            if not self.env.is_dev_mode():
                superadmin_password_file = self.env.SUPERADMIN_PASSWORD_FILE
                if not Path(superadmin_password_file).exists():
                    self.logger.error(
                        f"Superadmin password file {superadmin_password_file} not found."
                    )
                    return
                with open(superadmin_password_file) as file:
                    superadmin_password = file.read()
                try:
                    handler.execute_internal_action(
                        "user.set_password",
                        {"id": 1, "password": superadmin_password},
                    )
                except ActionException as e:
                    self.logger.error(f"Setting superadmin password failed: {e}")

    def dispatch_request(self, request: Request) -> Response | HTTPException:
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
            raise ViewException(f"Unknown type of response_body: {response_body}.")

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
