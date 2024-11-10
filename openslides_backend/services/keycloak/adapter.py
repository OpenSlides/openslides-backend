from os import environ

from .interface import IdpAdminService
from ..shared.authenticated_service import AuthenticatedService
from ...models.models import User
from ...shared.interfaces.logging import LoggingModule


class KeycloakAdminAdapter(IdpAdminService, AuthenticatedService):
    """
    Adapter to connect to the vote service.
    """

    def __init__(self, keycloak_url: str | None = None, logging: LoggingModule | None = None) -> None:
        self.url = keycloak_url if keycloak_url else environ.get("OPENSLIDES_KEYCLOAK_URL")
        self.logger = logging.getLogger(__name__) if logging else None

    def create_user(self, user: User) -> str:
        pass
