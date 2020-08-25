from typing import Optional, Tuple

import requests
import simplejson as json
from simplejson.errors import JSONDecodeError

from ..shared.exceptions import AuthenticationException
from ..shared.interfaces import Headers, LoggingModule

# TODO: Something should tell this service what the correct user id of the guest is.
GUEST_USER_ID = 0

AUTHENTICATION_HEADER = "Authentication"


class AuthenticationHTTPAdapter:
    """
    Adapter to connect to authentication service.
    """

    def __init__(self, authentication_url: str, logging: LoggingModule) -> None:
        self.url = authentication_url
        self.logger = logging.getLogger(__name__)
        self.headers = {"Content-Type": "application/json"}

    def get_user(self, headers: Headers) -> Tuple[int, Optional[str]]:
        """
        Fetches user id from authentication service using request headers.
        Returns a new access token, too, if one is received from auth service.
        """
        self.logger.debug(
            f"Start request to authentication service with the following data: {headers}"
        )
        request_data = json.dumps(headers.to_wsgi_list())
        access_token = None
        try:
            response = requests.post(
                self.get_internal_url("/api/authenticate"),
                data=request_data,
                headers=headers,
            )
        except requests.exceptions.ConnectionError as e:
            self.logger.debug(
                f"Cannot reach the authentication service on {self.url}. Error: {e}"
            )
            user_id = self.auth_is_down()
        else:
            # TODO: Check if we want to use self.auth_is_down() here too or if we want to raise HTTP 400 (at the moment we do so).
            if not response.ok:
                raise AuthenticationException(
                    f"Authentication service sends HTTP {response.status_code}. Please contact administrator."
                )
            try:
                body = response.json()
            except JSONDecodeError:
                raise AuthenticationException(
                    "Bad response from authentication service. Body does not contain JSON."
                )
            self.logger.debug(f"Get response body: {body}")

            try:
                user_id = body["userId"]
            except (TypeError, KeyError):
                raise AuthenticationException(
                    "Empty or bad response from authentication service."
                )
            access_token = response.headers.get(AUTHENTICATION_HEADER, None)
        return user_id, access_token

    def auth_is_down(self) -> int:
        """
        Fallback to guest mode if auth is down
        """
        self.logger.debug(f"Auth cannot be reached. Fall back to guest mode.")
        return GUEST_USER_ID

    def format_url_path(self, path: str) -> str:
        """
        Adds a '/' to the front of the given path, if not provided.
        """
        return f"/{path}" if not path.startswith("/") else path

    def get_internal_url(self, path: str) -> str:
        """
        Returns an internal url to a specified path at auth-service.
        """
        return f"{self.url}{self.format_url_path(path)}"
