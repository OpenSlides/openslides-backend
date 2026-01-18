from typing import Any, Optional

import requests

from .exceptions import ActionException
from .interfaces.logging import Logger


class KeycloakAdminClient:
    """Client for Keycloak Admin REST API."""

    def __init__(
        self, admin_api_url: str, access_token: str, logger: Optional[Logger] = None
    ):
        self.admin_api_url = admin_api_url.rstrip("/")
        self.access_token = access_token
        self.logger = logger

    def _make_request(
        self, method: str, endpoint: str, json_data: Optional[dict[str, Any]] = None
    ) -> requests.Response:
        """Make authenticated request with Bearer token."""
        url = f"{self.admin_api_url}/{endpoint}"
        if self.logger:
            self.logger.debug(f"Keycloak Admin API {method} request to: {url}")

        response = requests.request(
            method,
            url,
            json=json_data,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if self.logger:
            self.logger.debug(f"Keycloak Admin API response: {response.status_code}")

        return response

    def update_user(self, keycloak_id: str, user_data: dict[str, Any]) -> None:
        """
        Update user in Keycloak.

        Args:
            keycloak_id: The Keycloak user ID (UUID)
            user_data: Dictionary with Keycloak user fields to update

        Raises:
            ActionException: If the update fails
        """
        response = self._make_request("PUT", f"users/{keycloak_id}", user_data)
        if response.status_code != 204:
            raise ActionException(
                f"Keycloak user update failed: {response.status_code} - {response.text}"
            )

    def delete_user(self, keycloak_id: str) -> None:
        """
        Delete user in Keycloak.

        Args:
            keycloak_id: The Keycloak user ID (UUID)

        Raises:
            ActionException: If the deletion fails
        """
        response = self._make_request("DELETE", f"users/{keycloak_id}")
        if response.status_code != 204:
            raise ActionException(
                f"Keycloak user deletion failed: {response.status_code} - {response.text}"
            )
