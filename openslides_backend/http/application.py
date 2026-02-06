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

from ..services.auth.interface import AUTHENTICATION_HEADER, COOKIE_NAME

# OIDC session cookie name (used instead of auth service cookie in OIDC mode)
OIDC_SESSION_COOKIE = "openslides_session"
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
from .redirect_response import RedirectResponse
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
                return

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

            # If OIDC is enabled, sync users to Keycloak
            import os
            if is_truthy(os.environ.get("OIDC_ENABLED", "false")):
                self._sync_users_to_keycloak()

    def _sync_users_to_keycloak(self) -> None:
        """
        Sync local users to Keycloak after initial data import.
        Uses the migration 0101 data_manipulation function.
        Retries up to 30 times with 2 second delays if Keycloak isn't ready.
        """
        import io
        import time
        from importlib import import_module

        from openslides_backend.migrations.migration_helper import MigrationHelper
        from openslides_backend.services.postgresql.db_connection_handling import (
            get_new_os_conn,
        )

        max_retries = 30
        retry_delay = 2

        try:
            # Import the migration module (name starts with digit, need importlib)
            migration_module = import_module(
                "openslides_backend.migrations.migrations.0101_migrate_users_to_keycloak"
            )
            data_manipulation = migration_module.data_manipulation

            for attempt in range(max_retries):
                try:
                    self.logger.info(f"Syncing users to Keycloak (attempt {attempt + 1}/{max_retries})...")

                    # Set up a dummy stream for MigrationHelper.write_line()
                    stream = io.StringIO()
                    MigrationHelper.migrate_thread_stream = stream

                    with get_new_os_conn() as conn:
                        with conn.cursor() as curs:
                            data_manipulation(curs)
                            conn.commit()

                    # Log the migration output
                    output = stream.getvalue()
                    if output:
                        for line in output.strip().split("\n"):
                            self.logger.info(f"[Migration 0101] {line}")

                    MigrationHelper.migrate_thread_stream = None
                    self.logger.info("User sync to Keycloak completed")
                    return
                except Exception as e:
                    MigrationHelper.migrate_thread_stream = None
                    if "Connection refused" in str(e) or "Failed to establish" in str(e):
                        if attempt < max_retries - 1:
                            self.logger.info(f"Keycloak not ready, retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            continue
                    raise
        except ImportError as e:
            self.logger.warning(
                f"Migration 0101 not found, skipping Keycloak user sync: {e}"
            )
        except Exception as e:
            import traceback
            self.logger.error(f"Failed to sync users to Keycloak: {e}")
            self.logger.error(traceback.format_exc())

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

        # Handle RedirectResponse for OIDC provisioning flow
        if isinstance(response_body, RedirectResponse):
            self.logger.debug(
                f"Redirecting to {response_body.location} with status {response_body.status_code}"
            )
            response = Response(
                status=response_body.status_code,
                headers={"Location": response_body.location},
            )
            if response_body.access_token:
                response.headers[AUTHENTICATION_HEADER] = response_body.access_token
            if response_body.refresh_cookie:
                # Use OIDC session cookie for OIDC redirects
                response.set_cookie(
                    OIDC_SESSION_COOKIE,
                    response_body.refresh_cookie,
                    httponly=True,
                    secure=True,
                    samesite="Lax",  # Lax to allow redirect from Keycloak
                )
            return response

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
            if isinstance(access_token, tuple):
                # (access_token, refresh_cookie) tuple from OIDC who-am-i
                token, refresh_cookie = access_token
                response.headers[AUTHENTICATION_HEADER] = token
                if refresh_cookie:
                    response.set_cookie(
                        COOKIE_NAME,
                        refresh_cookie,
                        httponly=True,
                        secure=True,
                        samesite="Strict",
                    )
            else:
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
