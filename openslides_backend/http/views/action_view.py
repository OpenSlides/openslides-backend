import binascii
import os
from base64 import b64decode, b64encode
from pathlib import Path
from typing import Any

import requests

from ...action.action_handler import ActionHandler
from ...action.action_worker import handle_action_in_worker_thread
from ...i18n.translator import Translator
from ...migrations.migration_helper import MigrationHelper
from ...migrations.migration_manager import MigrationManager
from ...services.auth.interface import AUTHENTICATION_HEADER, COOKIE_NAME
from ...services.database.extended_database import ExtendedDatabase
from ...services.postgresql.db_connection_handling import get_new_os_conn
from ...shared.env import DEV_PASSWORD
from ...shared.exceptions import AuthenticationException, ServerError
from ...shared.filters import FilterOperator
from ...shared.interfaces.wsgi import RouteResponse
from ...shared.oidc_validator import OidcTokenValidator
from ...shared.util import ONE_ORGANIZATION_FQID
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
        Handle OIDC user provisioning and session creation after Keycloak login.

        This endpoint is called by Traefik after successful OIDC authentication.
        It validates the Keycloak token, provisions the user if needed,
        creates an OpenSlides session, and redirects to the original destination.

        Expected headers (set by Traefik OIDC middleware):
        - Authorization: Bearer <keycloak_access_token>

        Query parameters:
        - redirect_uri: Original URL to redirect to after provisioning (default: "/")

        Response:
        - HTTP 302 Redirect to redirect_uri with session cookies set
        - On error: HTTP 302 Redirect to /login?error=<message>
        """
        self.logger.debug("Start OIDC provisioning request.")

        # 1. Read redirect_uri from query parameter (fallback: "/")
        redirect_uri = request.args.get("redirect_uri", "/")

        # 2. Extract Bearer token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.lower().startswith("bearer "):
            self.logger.error("No Bearer token in Authorization header.")
            return RedirectResponse(location="/login?error=no_token"), None

        keycloak_token = auth_header[7:]  # Remove "Bearer " prefix

        # Use database connection context for datastore access
        with get_new_os_conn() as conn:
            datastore = ExtendedDatabase(conn, self.logging, self.env)

            # 3. Load OIDC config from organization
            try:
                organization = datastore.get(
                    ONE_ORGANIZATION_FQID,
                    [
                        "oidc_enabled",
                        "oidc_provider_url",
                        "oidc_client_id",
                        "oidc_client_secret",
                    ],
                    lock_result=False,
                )
            except Exception as e:
                self.logger.error(f"Failed to get organization settings: {e}")
                return RedirectResponse(location="/login?error=config_error"), None

            if not organization.get("oidc_enabled"):
                self.logger.debug("OIDC not enabled in organization settings.")
                return RedirectResponse(location="/login?error=oidc_disabled"), None

            provider_url = organization.get("oidc_provider_url")
            client_id = organization.get("oidc_client_id")

            if not provider_url or not client_id:
                self.logger.error("OIDC provider URL or client ID not configured.")
                return RedirectResponse(location="/login?error=oidc_not_configured"), None

            # 4. Validate token and extract keycloak_id (sub claim)
            try:
                validator = OidcTokenValidator(
                    provider_url=provider_url,
                    client_id=client_id,
                    client_secret=organization.get("oidc_client_secret"),
                )
                token_payload = validator.validate_token(keycloak_token)
                keycloak_id = token_payload.get("sub")
            except Exception as e:
                self.logger.error(f"Token validation failed: {e}")
                return RedirectResponse(location="/login?error=token_invalid"), None

            if not keycloak_id:
                self.logger.error("Missing 'sub' claim in token.")
                return RedirectResponse(location="/login?error=missing_sub"), None

            # 5. Get user info from Keycloak userinfo endpoint
            try:
                user_info = validator.get_user_info(keycloak_token)
            except Exception as e:
                self.logger.error(f"Failed to fetch user info: {e}")
                return RedirectResponse(location="/login?error=userinfo_failed"), None

            # 6. Look up user by keycloak_id in datastore
            try:
                users = datastore.filter(
                    "user",
                    FilterOperator("keycloak_id", "=", keycloak_id),
                    ["id", "username", "is_active"],
                    lock_result=False,
                )
            except Exception as e:
                self.logger.error(f"Failed to look up user: {e}")
                return RedirectResponse(location="/login?error=user_lookup_failed"), None

            user: dict[str, Any] | None = None

            if len(users) == 1:
                user = next(iter(users.values()))
                self.logger.debug(f"Found existing user with keycloak_id: {keycloak_id}")
            elif len(users) > 1:
                self.logger.error(f"Multiple users found with keycloak_id: {keycloak_id}")
                return RedirectResponse(location="/login?error=multiple_users"), None
            else:
                # 7. User not found - provision via user.save_keycloak_account action
                self.logger.debug(f"User not found, provisioning new user for keycloak_id: {keycloak_id}")
                try:
                    user_id = self._provision_oidc_user(keycloak_id, user_info)
                    if user_id:
                        user = {"id": user_id, "is_active": True}
                    else:
                        return RedirectResponse(location="/login?error=provision_failed"), None
                except Exception as e:
                    self.logger.error(f"Failed to provision user: {e}")
                    return RedirectResponse(location="/login?error=provision_failed"), None

            # 8. Check if user is active
            if not user.get("is_active", True):
                self.logger.debug(f"User account is deactivated: {user.get('id')}")
                return RedirectResponse(location="/login?error=user_deactivated"), None

        # 9. Create SSO session via auth service (outside db context)
        try:
            user_id = user["id"]
            access_token, refresh_cookie = self.services.authentication().sso_login(user_id)
            self.logger.debug(f"SSO login successful for user_id: {user_id}, redirecting to: {redirect_uri}")

            # 10. Return redirect response with session cookies
            return RedirectResponse(
                location=redirect_uri,
                access_token=access_token,
                refresh_cookie=refresh_cookie,
            ), None
        except Exception as e:
            self.logger.error(f"Failed to create SSO session: {e}")
            return RedirectResponse(location="/login?error=session_failed"), None

    @route("who-am-i", prefix="auth", method="POST", json=False)
    def oidc_who_am_i(self, request: Request) -> RouteResponse:
        """
        Handle who-am-i request - returns user info for existing session.

        This endpoint checks the existing OpenSlides session and returns user info.
        It does NOT perform user provisioning - that's handled by oidc-provision.

        Expected headers/cookies:
        - authentication header with OpenSlides access token, OR
        - refreshId cookie with OpenSlides refresh token

        Response format (API-compatible with auth service):
        - Success: {"success": true, "message": "Action handled successfully"}
          + authentication header with access token
        - Anonymous: {"success": true, "message": "anonymous"}
        - Error: {"success": false, "message": "<error_message>"}
        """
        self.logger.debug("Start who-am-i request.")

        # Check for existing OpenSlides session via auth service
        try:
            user_id, access_token = self.get_user_id_from_headers(
                request.headers, request.cookies
            )

            if user_id and user_id > 0:
                self.logger.debug(f"User authenticated via session: user_id={user_id}")
                return {"success": True, "message": "Action handled successfully"}, access_token

            # No valid session found
            self.logger.debug("No valid session found, returning anonymous.")
            return {"success": True, "message": "anonymous"}, None

        except Exception as e:
            self.logger.error(f"Session check failed: {e}")
            return {"success": True, "message": "anonymous"}, None

    def _provision_oidc_user(
        self, keycloak_id: str, user_info: dict[str, Any]
    ) -> int | None:
        """
        Provision a new user via the internal save_keycloak_account action.
        """
        # Prepare the action data from user_info
        action_data = {
            "keycloak_id": keycloak_id,
            "email": user_info.get("email"),
            "given_name": user_info.get("given_name"),
            "family_name": user_info.get("family_name"),
            "preferred_username": user_info.get("preferred_username"),
            "name": user_info.get("name"),
        }

        # Remove None values
        action_data = {k: v for k, v in action_data.items() if v is not None}

        # Get internal auth password
        internal_password = self._get_internal_auth_password()

        # Make internal HTTP request to the action endpoint
        action_port = os.environ.get("ACTION_PORT", "9002")
        action_url = f"http://localhost:{action_port}/internal/handle_request"

        response = requests.post(
            action_url,
            json=[
                {
                    "action": "user.save_keycloak_account",
                    "data": [action_data],
                }
            ],
            headers={
                "Authorization": b64encode(internal_password.encode()).decode(),
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if response.status_code != 200:
            self.logger.error(
                f"Failed to provision user: HTTP {response.status_code} - {response.text}"
            )
            raise Exception(f"Failed to provision user: HTTP {response.status_code}")

        result = response.json()
        if result.get("success") and result.get("results"):
            action_results = result["results"]
            if action_results and action_results[0]:
                return action_results[0][0].get("user_id")

        return None

    def _get_internal_auth_password(self) -> str:
        """Get the internal authentication password."""
        if self.env.is_dev_mode():
            return DEV_PASSWORD
        filename = self.env.INTERNAL_AUTH_PASSWORD_FILE
        if filename:
            with open(filename) as f:
                return f.read().strip()
        raise ServerError("Internal authentication not configured")

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
