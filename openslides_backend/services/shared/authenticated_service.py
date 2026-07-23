from abc import abstractmethod
from typing import Protocol

class AuthenticatedServiceInterface(Protocol):
    access_token: str

    @abstractmethod
    def set_authentication(self, access_token: str) -> None:
        """Set the needed authentication details from the request data."""


class AuthenticatedService(AuthenticatedServiceInterface):
    def set_authentication(self, access_token: str) -> None:
        self.access_token = access_token

    def get_auth_header(self) -> dict[str, str]:
        return {"Authorization": self.access_token}
