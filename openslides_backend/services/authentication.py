import requests
import simplejson as json
from simplejson.errors import JSONDecodeError  # type: ignore

from ..shared.exceptions import AuthenticationException
from ..shared.interfaces import Headers, LoggingModule


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
        response = requests.post(
            self.url, data=json.dumps(headers.to_wsgi_list()), headers=self.headers
        )
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
        return user_id
