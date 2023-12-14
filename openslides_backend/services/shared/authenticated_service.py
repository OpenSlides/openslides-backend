from abc import abstractmethod
from typing import Dict, Protocol

from authlib import AUTHENTICATION_HEADER, COOKIE_NAME


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

    def get_auth_header(self) -> Dict[str, str]:
        return {AUTHENTICATION_HEADER: self.access_token}

    def get_auth_cookie(self) -> Dict[str, str]:
        return {COOKIE_NAME: self.refresh_id}
