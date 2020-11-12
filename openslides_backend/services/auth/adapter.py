from typing import Dict, Optional, Tuple

from authlib import AuthHandler
from authlib.constants import ANONYMOUS_USER, AUTHENTICATION_HEADER  # noqa
from authlib.exceptions import AuthenticateException, InvalidCredentialsException

from ...shared.exceptions import AuthenticationException as BackendAuthException
from ...shared.interfaces.logging import LoggingModule
from ...shared.interfaces.wsgi import Headers
from .interface import AuthenticationService


class AuthenticationHTTPAdapter(AuthenticationService):
    """
    Adapter to connect to authentication service.
    """

    def __init__(self, logging: LoggingModule) -> None:
        self.logger = logging.getLogger(__name__)
        self.auth_handler = AuthHandler(self.logger.debug)
        self.headers = {"Content-Type": "application/json"}

    def authenticate(
        self, headers: Headers, cookies: Dict[str, str]
    ) -> Tuple[int, Optional[str]]:
        """
        Fetches user id from authentication service using request headers.
        Returns a new access token, too, if one is received from auth service.
        """

        self.logger.debug(
            f"Start request to authentication service with the following data: {headers}"
        )
        try:
            return self.auth_handler.authenticate(headers, cookies)
        except (AuthenticateException, InvalidCredentialsException) as e:
            self.logger.debug(f"Error in auth service: {e.message}")
            raise BackendAuthException(e.message)

    def hash(self, toHash: str) -> str:
        return self.auth_handler.hash(toHash)

    def is_equals(self, toHash: str, toCompare: str) -> bool:
        return self.auth_handler.is_equals(toHash, toCompare)

    def is_anonymous(self, user_id: int) -> bool:
        return user_id == ANONYMOUS_USER
