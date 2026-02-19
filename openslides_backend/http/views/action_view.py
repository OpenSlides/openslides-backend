import binascii
import os
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
from ...shared.exceptions import AuthenticationException, ServerError, View400Exception
from ...shared.interfaces.wsgi import RouteResponse
from ..http_exceptions import Unauthorized
from ..redirect_response import RedirectResponse
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

    @route("oidc-provision", prefix="auth", method="GET", json=False)
    def oidc_provision_route(self, request: Request) -> RouteResponse:
        """
        Handle OIDC redirect after Keycloak login.

        This endpoint is called by Traefik after successful OIDC authentication.
        The actual token validation and user provisioning happens in
        get_user_id_from_headers() on subsequent requests.

        Query parameters:
        - redirect_uri: Original URL to redirect to (default: "/")

        Response:
        - HTTP 302 Redirect to redirect_uri
        """
        self.logger.debug("OIDC provision redirect.")
        redirect_uri = request.args.get("redirect_uri", "/")
        return RedirectResponse(location=redirect_uri), None

    @route("who-am-i", prefix="auth", method="POST", json=False)
    def oidc_who_am_i(self, request: Request) -> RouteResponse:
        """
        Handle who-am-i request - validates Bearer token and returns user info.

        In OIDC mode, validates the Bearer token from Authorization header via JWKS.

        Response format (API-compatible with auth service):
        - Success: {"success": true, "message": "Action handled successfully"}
        - Anonymous: {"success": true, "message": "anonymous"}
        """
        self.logger.debug("Start OIDC who-am-i request.")

        user_id, _ = self.get_user_id_from_headers(request.headers, request.cookies)
        if user_id and user_id > 0:
            self.logger.debug(f"User authenticated: user_id={user_id}")
            return {"success": True, "message": "Action handled successfully", "user_id": user_id}, None

        self.logger.debug("No valid session found, returning anonymous.")
        return {"success": True, "message": "anonymous"}, None

    @route("oidc-backchannel-logout", prefix="auth", method="POST", json=False)
    def oidc_backchannel_logout(self, request: Request) -> RouteResponse:
        """
        Handle OIDC backchannel logout from Keycloak.

        This endpoint receives logout tokens from Keycloak when a user's session
        is terminated (e.g., via admin console or logout from another client).
        The session ID is extracted and stored in both the local cache and
        Redis for Go services to pick up.

        Request:
        - Content-Type: application/x-www-form-urlencoded
        - Body: logout_token=<JWT>

        Response:
        - 200 OK with {"status": "ok"} on success
        - 400 Bad Request if logout_token is missing or OIDC not configured
        """
        from ...shared.oidc_validator import get_oidc_validator
        from .base_view import invalidate_session

        # Get logout_token from form data
        logout_token = request.form.get("logout_token")
        if not logout_token:
            raise View400Exception("Missing logout_token")

        validator = get_oidc_validator()
        if not validator:
            raise View400Exception("OIDC not configured")

        # Validate the logout token and extract session ID
        payload = validator.validate_logout_token(logout_token)
        session_id = payload["sid"]

        # 1. Invalidate in Redis (used by Python workers for session checks)
        invalidate_session(session_id)

        # 2. Publish to Redis logout stream (for Go services)
        from .base_view import _get_redis
        r = _get_redis()
        r.xadd("logout", {"sessionId": session_id})

        self.logger.info(f"Backchannel logout: session {session_id} invalidated")
        return {"status": "ok"}, None

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
