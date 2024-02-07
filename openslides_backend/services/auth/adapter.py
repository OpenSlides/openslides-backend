from urllib import parse

from authlib import (
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
    """

    def __init__(self, logging: LoggingModule) -> None:
        self.logger = logging.getLogger(__name__)
        self.auth_handler = AuthHandler(self.logger.debug)
        self.headers = {"Content-Type": "application/json"}

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

    def authenticate_only_refresh_id(self) -> int:
        self.logger.debug(
            f"Start request to authentication service with the following cookie: {self.refresh_id}"
        )
        try:
            return self.auth_handler.authenticate_only_refresh_id(
                parse.unquote(self.refresh_id)
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
