from typing import Any, Literal

import requests
import simplejson as json

from ...shared.exceptions import VoteServiceException
from ...shared.interfaces.logging import LoggingModule
from ..request_methods import REQUEST_METHOD
from ..shared.authenticated_service import AuthenticatedService
from .interface import VoteService


class VoteAdapter(VoteService, AuthenticatedService):
    """
    Adapter to connect to the vote service.
    """

    def __init__(self, vote_url: str, logging: LoggingModule) -> None:
        self.url = vote_url
        self.logger = logging.getLogger(__name__)

    def retrieve(
        self,
        endpoint: str,
        request_method: Literal[
            REQUEST_METHOD.POST, REQUEST_METHOD.DELETE
        ] = REQUEST_METHOD.POST,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        response = self.make_request(endpoint, request_method, payload)
        message = f"Vote service sends HTTP {response.status_code} with the following content: {str(response.content)}."
        if response.status_code < 400:
            self.logger.debug(message)
        elif response.status_code == 500:
            self.logger.error(message)
            raise VoteServiceException(
                f"Vote service sends HTTP 500 Internal Server Error with the message: {message}."
            )
        else:
            self.logger.error(message)
            raise VoteServiceException(message)
        if response.content:
            return response.json()

    def make_request(
        self,
        endpoint: str,
        request_method: Literal[REQUEST_METHOD.POST, REQUEST_METHOD.DELETE],
        payload: dict[str, Any] | None = None,
    ) -> Any:
        if not self.access_token or not self.refresh_id:
            raise VoteServiceException("You must be logged in to vote")
        payload_json = json.dumps(payload, separators=(",", ":")) if payload else None
        try:
            if request_method == REQUEST_METHOD.DELETE:
                return requests.delete(
                    url=endpoint,
                    headers={
                        "Content-Type": "application/json",
                        **self.get_auth_header(),
                    },
                    cookies=self.get_auth_cookie(),
                )
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

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        endpoint = self.get_endpoint()
        return self.retrieve(endpoint, payload=payload)

    def update(self, id: int, payload: dict[str, Any]) -> dict[str, Any]:
        endpoint = self.get_endpoint(id)
        return self.retrieve(endpoint, payload=payload)

    def delete(self, id: int) -> dict[str, Any]:
        endpoint = self.get_endpoint(id)
        return self.retrieve(endpoint, REQUEST_METHOD.DELETE)

    def start(self, id: int) -> dict[str, Any]:
        endpoint = self.get_endpoint(id, "start")
        return self.retrieve(endpoint)

    def finalize(
        self,
        id: int,
        optional_attributes: list[Literal["publish", "anonymize"]] = [],
    ) -> dict[str, Any]:
        endpoint = self.get_endpoint(id, "finalize")
        if optional_attributes:
            endpoint += f"?{'&'.join(optional_attributes)}"
        return self.retrieve(endpoint)

    def reset(self, id: int) -> dict[str, Any]:
        endpoint = self.get_endpoint(id, "reset")
        return self.retrieve(endpoint)

    def vote(self, id: int) -> dict[str, Any]:
        endpoint = self.get_endpoint(id, "vote")
        return self.retrieve(endpoint)

    def get_endpoint(self, id: int | None = None, route: str | None = None) -> str:
        return (
            f"{self.url}/poll"
            + (f"/{id}" if id else "")
            + (f"/{route}" if route else "")
        )
