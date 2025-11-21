import binascii
from base64 import b64decode
from pathlib import Path

from ...action.action_handler import ActionHandler
from ...action.action_worker import handle_action_in_worker_thread
from ...i18n.translator import Translator
from ...migrations.migration_helper import MigrationHelper
from ...migrations.migration_manager import MigrationManager
from ...services.auth.interface import AUTHENTICATION_HEADER, COOKIE_NAME
from ...services.postgresql.db_connection_handling import get_new_os_conn
from ...shared.env import DEV_PASSWORD
from ...shared.exceptions import AuthenticationException, ServerError
from ...shared.interfaces.wsgi import RouteResponse
from ..http_exceptions import Unauthorized
from ..request import Request
from .base_view import BaseView, route

INTERNAL_AUTHORIZATION_HEADER = "Authorization"


VERSION_PATH = Path(__file__).parent / ".." / ".." / "version.txt"


class ActionView(BaseView):
    """
    The ActionView receives a bundle of actions via HTTP and handles it to the
    ActionHandler after retrieving request user id.
    """

    @route(["handle_request", "handle_separately"])
    def action_route(self, request: Request) -> RouteResponse:
        self.logger.debug("Start dispatching action request.")

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                MigrationHelper.assert_migration_index(curs)
        # Get user id.
        user_id, access_token = self.get_user_id_from_headers(
            request.headers, request.cookies
        )
        # Set Headers and Cookies in services.
        self.services.vote().set_authentication(
            request.headers.get(AUTHENTICATION_HEADER, ""),
            request.cookies.get(COOKIE_NAME, ""),
        )

        # Handle request.
        handler = ActionHandler(self.env, self.services, self.logging)
        Translator.set_translation_language(request.headers.get("Accept-Language"))
        is_atomic = not request.environ["RAW_URI"].endswith("handle_separately")
        response = handle_action_in_worker_thread(
            request.json, user_id, is_atomic, handler
        )
        return response, access_token

    @route("handle_request", internal=True)
    def internal_action_route(self, request: Request) -> RouteResponse:
        self.logger.debug("Start dispatching internal action request.")

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                MigrationHelper.assert_migration_index(curs)
        self.check_internal_auth_password(request)

        handler = ActionHandler(self.env, self.services, self.logging)
        is_atomic = True  # handle_separately not accepted as route
        response = handle_action_in_worker_thread(
            request.json, -1, is_atomic, handler, internal=True
        )
        self.logger.debug("Internal action request finished successfully.")
        return response, None

    @route("migrations", internal=True)
    def migrations_route(self, request: Request) -> RouteResponse:
        self.logger.debug("Start executing migrations request.")
        self.check_internal_auth_password(request)
        manager = MigrationManager(self.env, self.services, self.logging)
        response = manager.handle_request(request.json)
        self.logger.debug("Migrations request finished successfully.")
        return {"success": True, **response}, None

    @route("health", method="GET", json=False)
    def health_route(self, request: Request) -> RouteResponse:
        return {"status": "running"}, None

    @route("info", method="GET", json=False)
    def info_route(self, request: Request) -> RouteResponse:
        return {"healthinfo": {"actions": dict(ActionHandler.get_health_info())}}, None

    @route("version", method="GET", json=False)
    def version_route(self, _: Request) -> RouteResponse:
        with open(VERSION_PATH) as file:
            version = file.read().strip()
            return {"version": version}, None

    def check_internal_auth_password(self, request: Request) -> None:
        request_password = request.headers.get(INTERNAL_AUTHORIZATION_HEADER)
        if self.env.is_dev_mode():
            secret_password = DEV_PASSWORD
        else:
            filename = self.env.INTERNAL_AUTH_PASSWORD_FILE
            if not filename:
                raise ServerError("Missing INTERNAL_AUTH_PASSWORD_FILE.")
            with open(filename) as file_:
                secret_password = file_.read()
        if request_password is not None:
            try:
                decoded_password = b64decode(request_password).decode()
            except (UnicodeDecodeError, binascii.Error):
                raise AuthenticationException(
                    "The internal auth password must be correctly base64-encoded."
                )
            if decoded_password == secret_password:
                return
        raise Unauthorized()
