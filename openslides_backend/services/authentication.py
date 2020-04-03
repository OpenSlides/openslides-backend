import requests
import simplejson as json
from simplejson.errors import JSONDecodeError  # type: ignore

from ..shared.exceptions import AuthenticationException
from ..shared.interfaces import Headers, LoggingModule

# TODO: Something should tell this service what the correct user id of the guest is.
GUEST_USER_ID = 0


class AuthenticationHTTPAdapter:
    """
    Adapter to connect to authentication service.
    """

    def __init__(self, authentication_url: str, logging: LoggingModule) -> None:
        self.url = authentication_url
        self.logger = logging.getLogger(__name__)
        self.headers = {"Content-Type": "application/json"}

    def get_user(self, headers: Headers) -> int:
        """
        Fetches user id from authentication service using request headers.
        """
        self.logger.debug(
            f"Start request to authentication service with the following data: {headers}"
        )

        if self.is_auth_accessible(self.url):
            request_data = json.dumps(headers.to_wsgi_list())
            response = requests.post(self.url, data=request_data, headers=self.headers)
            if not response.ok:
                raise AuthenticationException(
                    f"Authentication service sends HTTP {response.status_code}."
                )
            try:
                body = response.json()
            except JSONDecodeError:
                raise AuthenticationException(
                    "Bad response from authentication service. Body does not contain JSON."
                )
            self.logger.debug(f"Get repsonse: {body}")
            try:
                user_id = body["user_id"]
            except (TypeError, KeyError):
                raise AuthenticationException(
                    "Empty or bad response from authentication service."
                )
        else:
            self.logger.debug(f"Auth cannot be reached. Fall back to guest mode.")
            user_id = GUEST_USER_ID
        return user_id

    def is_auth_accessible(self, url: str) -> bool:
        """
        Checks if authentication service is accessible.
        """
        try:
            response = requests.head(url)
        except requests.exceptions.ConnectionError as e:
            self.logger.debug(
                f"Cannot reach the authentication service on {url}. Error: {e}"
            )
            return False
        return response.status_code == 200
