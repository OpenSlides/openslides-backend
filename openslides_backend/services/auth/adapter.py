from typing import Optional
from urllib import parse

from osauthlib import (
    ANONYMOUS_USER,
    AUTHORIZATION_HEADER,
    AuthenticateException,
    AuthHandler,
    AuthorizationException,
    InvalidCredentialsException,
)

from ...shared.exceptions import AuthenticationException
from ...shared.interfaces.logging import LoggingModule
from ..shared.authenticated_service import AuthenticatedService
from .interface import AuthenticationService


class AuthenticationHTTPAdapter(AuthenticationService, AuthenticatedService):
    """
    Adapter to connect to authentication service.

    Supports both OpenSlides tokens (HS256) and OIDC/Keycloak tokens (RS256).
    """

    def __init__(self, logging: LoggingModule) -> None:
        self.logger = logging.getLogger(__name__)
        self.auth_handler = AuthHandler(self.logger.debug)
        self.headers = {"Content-Type": "application/json"}
        self._oidc_configured = False

    def configure_oidc(
        self, oidc_enabled: bool, provider_url: Optional[str], client_id: Optional[str]
    ) -> None:
        """
        Configure OIDC authentication from organization settings.

        Args:
            oidc_enabled: Whether OIDC is enabled
            provider_url: Keycloak realm URL
            client_id: OIDC client ID
        """
        if oidc_enabled and provider_url and client_id:
            self.logger.debug(
                f"Configuring OIDC authentication: issuer={provider_url}, audience={client_id}"
            )
            self.auth_handler.configure_oidc(
                issuer=provider_url, audience=client_id
            )
            self._oidc_configured = True
        else:
            self._oidc_configured = False

    def authenticate(self) -> tuple[int, str | None]:
        """
        Fetches user id from authentication service using request headers.
        Returns a new access token, too, if one is received from auth service.
        """
        self.logger.debug(
            f"Start request to authentication service with the following data: access_token: {self.access_token}, cookie: {self.refresh_id}"
        )
        try:
            return self.auth_handler.authenticate(
                self.access_token, parse.unquote(self.refresh_id)
            )
        except (AuthenticateException, InvalidCredentialsException) as e:
            self.logger.debug(f"Error in auth service: {e.message}")
            raise AuthenticationException(e.message)

    def hash(self, toHash: str) -> str:
        return self.auth_handler.hash(toHash)

    def is_equal(self, toHash: str, toCompare: str) -> bool:
        return self.auth_handler.is_equal(toHash, toCompare)

    def is_anonymous(self, user_id: int) -> bool:
        return user_id == ANONYMOUS_USER

    def create_authorization_token(self, user_id: int, email: str) -> str:
        try:
            response = self.auth_handler.create_authorization_token(user_id, email)
        except AuthenticateException as e:
            raise AuthenticationException(e.message)
        return response.headers.get(AUTHORIZATION_HEADER, "")

    def verify_authorization_token(self, user_id: int, token: str) -> bool:
        try:
            found_user_id, _ = self.auth_handler.verify_authorization_token(token)
        except (AuthenticateException, AuthorizationException) as e:
            raise AuthenticationException(e.message)
        return user_id == found_user_id

    def clear_all_sessions(self) -> None:
        self.auth_handler.clear_all_sessions(
            self.access_token, parse.unquote(self.refresh_id)
        )

    def clear_sessions_by_user_id(self, user_id: int) -> None:
        self.auth_handler.clear_sessions_by_user_id(user_id)

    def sso_login(self, user_id: int) -> tuple[str, str]:
        """
        Create a session for a user via SSO (OIDC/SAML) login.
        """
        self.logger.debug(f"SSO login for user_id: {user_id}")
        try:
            access_token, refresh_cookie = self.auth_handler.sso_login(user_id)
            self.logger.debug(f"SSO login successful: access_token={access_token[:30]}..., refresh_cookie={refresh_cookie[:30] if refresh_cookie else 'None'}...")
            return access_token, refresh_cookie
        except AuthenticateException as e:
            raise AuthenticationException(e.message)
