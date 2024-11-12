from os import environ

from .interface import IdpAdminService
from ..shared.authenticated_service import AuthenticatedService
from ...shared.interfaces.logging import LoggingModule


class KeycloakAdminAdapter(IdpAdminService, AuthenticatedService):
    """
    Adapter to connect to the vote service.
    """

    def __init__(self, keycloak_url: str | None = None, logging: LoggingModule | None = None) -> None:
        self.url = keycloak_url if keycloak_url else environ.get("OPENSLIDES_KEYCLOAK_URL")
        self.logger = logging.getLogger(__name__) if logging else None

    def create_user(self, username: str, password_hash: str, saml_id: str | None) -> str:
        ARGON2_HASH_START = "$argon2"
        '''
        def is_sha512_hash(self, hash: str) -> bool:
            return (
                not hash.startswith(ARGON2_HASH_START) and len(hash) == SHA512_HASHED_LENGTH
            )

        def is_argon2_hash(self, hash: str) -> bool:
            return hash.startswith(ARGON2_HASH_START)
        '''
        pass

