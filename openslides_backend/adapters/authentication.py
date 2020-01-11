import requests
import simplejson as json

from .. import logging
from ..exceptions import AuthException
from .providers import HeadersProvider

logger = logging.getLogger(__name__)


class AuthenticationAdapter:
    """
    Adapter to connect to authentication service.
    """

    def __init__(self, authentication_url: str) -> None:
        self.url = authentication_url
        self.headers = {"Content-Type": "application/json"}

    def get_user(self, headers: HeadersProvider) -> int:
        logger.debug(
            f"Start request to authentication service with the following data: {headers}"
        )
        response = requests.post(
            self.url, data=json.dumps(headers.to_wsgi_list()), headers=self.headers
        )
        body = response.json()
        logger.debug(f"Get repsonse: {body}")
        try:
            user_id = body["user_id"]
        except (TypeError, KeyError):
            raise AuthException("Bad response from authentication service.")
        return user_id
