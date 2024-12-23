from abc import abstractmethod
from typing import Any, Protocol

from datastore.shared.di import service_interface
from ..shared.authenticated_service import AuthenticatedServiceInterface
from ...models.models import User


@service_interface
class IdpAdminService(AuthenticatedServiceInterface, Protocol):
    """
    Interface of a idp admin service.
    """

    @abstractmethod
    def create_user(self, username: str, password_hash: str, saml_id: str | None) -> str:
        """Create user and return new IDP user ID"""
