import binascii
import json
from base64 import b64decode
from pathlib import Path

from os_authlib.message_bus import MessageBus
from ...action.action_handler import ActionHandler
from ...action.action_worker import handle_action_in_worker_thread
from ...i18n.translator import Translator
from ...migrations import assert_migration_index
from ...migrations.migration_handler import MigrationHandler
from ...services.auth.interface import AUTHENTICATION_HEADER, COOKIE_NAME
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_bus = MessageBus()

    @route(["handle_request", "handle_separately"])
    def action_route(self, request: Request) -> RouteResponse:
        self.logger.debug("Start dispatching action request.")

        assert_migration_index()

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

        assert_migration_index()
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
        handler = MigrationHandler(self.env, self.services, self.logging)
        response = handler.handle_request(request.json)
        self.logger.debug("Migrations request finished successfully.")
        return {"success": True, **response}, None

    @route("health", method="GET", json=False)
    def health_route(self, request: Request) -> RouteResponse:
        return {"status": "running"}, None

    @route("info", method="GET", json=False)
    def info_route(self, request: Request) -> RouteResponse:
        return {"healthinfo": {"actions": dict(ActionHandler.get_health_info())}}, None

    @route("logout", method="POST", json=False)
    def backchannel_logout(self, request: Request) -> RouteResponse:
        # topic '<logout>', field 'sessionId', value sessionId
        self.logger.debug("Received logout request")
        try:
            logout_token = request.form.get("logout_token")
            if not logout_token:
                self.logger.error("Missing logout_token")
                raise ServerError("Missing logout_token")

            # Verify and decode the logout token
            decoded_token = self.services.authentication().auth_handler.verify_logout_token(logout_token)
            if decoded_token is None:
                return AuthenticationException("Invalid logout token")

            # Extract the session ID (sid) from the token
            session_id = decoded_token.get("sid")
            if not session_id:
                return AuthenticationException("Missing session ID (sid) in logout token")

            self.logger.debug(f"Session ID to terminate: {session_id}")
            self.message_bus.redis.xadd("logout",  {"sessionId": session_id})

            return { "success": True }, None
        except json.JSONDecodeError:
            return ServerError("Invalid JSON payload", status=400)

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
