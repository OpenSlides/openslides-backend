import json
from typing import Any, Dict, Optional

import requests
from authlib import COOKIE_NAME, HEADER_NAME

from ...shared.exceptions import VoteServiceException
from ...shared.interfaces.logging import LoggingModule
from ...shared.interfaces.wsgi import Headers
from .interface import VoteService


class VoteAdapter(VoteService):
    """
    Adapter to connect to the vote service.
    """

    def __init__(self, vote_url: str, logging: LoggingModule) -> None:
        self.url = vote_url
        self.logger = logging.getLogger(__name__)

    def retrieve(self, endpoint: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        response = self.make_request(endpoint, payload)
        message = f"Vote service sends HTTP {response.status_code} with the following content: {str(response.content)}."
        if response.status_code < 400:
            self.logger.debug(message)
        else:
            self.logger.error(message)
            raise VoteServiceException(message)
        if response.content:
            return response.json()

    def make_request(
        self, endpoint: str, payload: Optional[Dict[str, Any]] = None
    ) -> Any:
        if not self.access_token or not self.cookie:
            raise VoteServiceException("You must be logged in to vote")
        payload_json = json.dumps(payload, separators=(",", ":")) if payload else None
        try:
            return requests.post(
                url=endpoint,
                data=payload_json,
                headers={
                    "Content-Type": "application/json",
                    HEADER_NAME: self.access_token,
                },
                cookies={COOKIE_NAME: self.cookie},
            )
        except requests.exceptions.ConnectionError as e:
            self.logger.error(
                f"Cannot reach the vote service on {endpoint}. Error: {e}"
            )
            raise VoteServiceException(f"Cannot reach the vote service on {endpoint}.")

    def set_authentication(self, headers: Headers, cookies: Dict) -> None:
        self.access_token = headers.get(HEADER_NAME, None)
        self.cookie = cookies.get(COOKIE_NAME, "")

    def start(self, id: int) -> None:
        endpoint = self.get_endpoint("create", id)
        self.retrieve(endpoint)

    def stop(self, id: int) -> Dict[str, Any]:
        endpoint = self.get_endpoint("stop", id)
        return self.retrieve(endpoint)

    def clear(self, id: int) -> None:
        endpoint = self.get_endpoint("clear", id)
        self.retrieve(endpoint)

    def clear_all(self) -> None:
        endpoint = self.get_endpoint("clear_all")
        self.retrieve(endpoint)

    def get_endpoint(self, route: str, id: Optional[int] = None) -> str:
        return f"{self.url}/{route}" + (f"?id={id}" if id else "")
