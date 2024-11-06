from typing import Any

import requests
import simplejson as json

from ...shared.exceptions import VoteServiceException
from ...shared.interfaces.logging import LoggingModule
from ..shared.authenticated_service import AuthenticatedService
from .interface import KeycloakAdminService


class KeycloakAdminAdapter(KeycloakAdminService, AuthenticatedService):
    """
    Adapter to connect to the vote service.
    """

    def __init__(self, vote_url: str, logging: LoggingModule) -> None:
        self.url = vote_url
        self.logger = logging.getLogger(__name__)

    def retrieve(self, endpoint: str, payload: dict[str, Any] | None = None) -> Any:
        response = self.make_request(endpoint, payload)
        message = f"Vote service sends HTTP {response.status_code} with the following content: {str(response.content)}."
        if response.status_code < 400:
            self.logger.debug(message)
        elif response.status_code == 500:
            self.logger.error(message)
            raise VoteServiceException(
                "Vote service sends HTTP 500 Internal Server Error."
            )
        else:
            self.logger.error(message)
            raise VoteServiceException(message)
        if response.content:
            return response.json()

    def make_request(self, endpoint: str, payload: dict[str, Any] | None = None) -> Any:
        if not self.access_token or not self.refresh_id:
            raise VoteServiceException("You must be logged in to vote")
        payload_json = json.dumps(payload, separators=(",", ":")) if payload else None
        try:
            return requests.post(
                url=endpoint,
                data=payload_json,
                headers={
                    "Content-Type": "application/json",
                    **self.get_auth_header(),
                },
                cookies=self.get_auth_cookie(),
            )
        except requests.exceptions.ConnectionError as e:
            self.logger.error(
                f"Cannot reach the vote service on {endpoint}. Error: {e}"
            )
            raise VoteServiceException(f"Cannot reach the vote service on {endpoint}.")

    def start(self, id: int) -> None:
        endpoint = self.get_endpoint("start", id)
        self.retrieve(endpoint)

    def stop(self, id: int) -> dict[str, Any]:
        endpoint = self.get_endpoint("stop", id)
        return self.retrieve(endpoint)

    def clear(self, id: int) -> None:
        endpoint = self.get_endpoint("clear", id)
        self.retrieve(endpoint)

    def clear_all(self) -> None:
        endpoint = self.get_endpoint("clear_all")
        self.retrieve(endpoint)

    def get_endpoint(self, route: str, id: int | None = None) -> str:
        return f"{self.url}/{route}" + (f"?id={id}" if id else "")
