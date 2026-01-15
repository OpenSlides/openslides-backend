from abc import abstractmethod
from typing import Protocol

from osauthlib import AUTHENTICATION_HEADER, COOKIE_NAME


class AuthenticatedServiceInterface(Protocol):
    access_token: str
    refresh_id: str

    @abstractmethod
    def set_authentication(self, access_token: str, refresh_id: str) -> None:
        """Set the needed authentication details from the request data."""


class AuthenticatedService(AuthenticatedServiceInterface):
    def set_authentication(self, access_token: str, refresh_id: str) -> None:
        self.access_token = access_token
        self.refresh_id = refresh_id

    def get_auth_header(self) -> dict[str, str]:
        return {AUTHENTICATION_HEADER: self.access_token}

    def get_auth_cookie(self) -> dict[str, str]:
        return {COOKIE_NAME: self.refresh_id}
