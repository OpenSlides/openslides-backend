from typing import Any, Optional

import requests

from .exceptions import ActionException
from .interfaces.logging import Logger


class KeycloakAdminClient:
    """Client for Keycloak Admin REST API.

    Supports two authentication modes:
    1. Direct access token (legacy): Pass access_token directly
    2. Client credentials (recommended): Pass client_id and client_secret to obtain
       a token via client credentials grant. The client must have service account
       enabled and realm-admin role assigned.
    """

    def __init__(
        self,
        admin_api_url: str,
        access_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_url: Optional[str] = None,
        logger: Optional[Logger] = None,
    ):
        self.admin_api_url = admin_api_url.rstrip("/")
        self.logger = logger
        self._access_token = access_token
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_url = token_url

        # If client credentials are provided, get token immediately
        if client_id and client_secret and not access_token:
            self._access_token = self._get_client_credentials_token()

    @property
    def access_token(self) -> str:
        """Get the access token, refreshing if using client credentials."""
        if not self._access_token:
            raise ActionException("No access token available for Keycloak Admin API")
        return self._access_token

    def _get_client_credentials_token(self) -> str:
        """Get access token using client credentials grant."""
        if not self._token_url:
            # Derive token URL from admin_api_url
            # admin_api_url: http://keycloak:8080/auth/admin/realms/openslides
            # token_url: http://keycloak:8080/auth/realms/openslides/protocol/openid-connect/token
            base_url = self.admin_api_url.split("/admin/")[0]
            realm = self.admin_api_url.split("/realms/")[-1]
            self._token_url = f"{base_url}/realms/{realm}/protocol/openid-connect/token"

        if self.logger:
            self.logger.debug(f"Getting client credentials token from: {self._token_url}")

        response = requests.post(
            self._token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )

        if response.status_code != 200:
            raise ActionException(
                f"Failed to get Keycloak admin token: {response.status_code} - {response.text}"
            )

        data = response.json()
        return data["access_token"]

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

    def create_user(self, user_data: dict[str, Any]) -> str:
        """
        Create user in Keycloak.

        Args:
            user_data: Dictionary with Keycloak user fields (username, email,
                       firstName, lastName, enabled, etc.)

        Returns:
            The Keycloak user ID (UUID) extracted from the Location header

        Raises:
            ActionException: If the creation fails
        """
        url = f"{self.admin_api_url}/users"
        if self.logger:
            self.logger.debug(f"Keycloak Admin API POST request to: {url}")

        # Ensure requiredActions is empty to prevent VERIFY_PROFILE blocking login
        user_data_with_defaults = {
            "requiredActions": [],
            **user_data,
        }

        response = requests.post(
            url,
            json=user_data_with_defaults,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if self.logger:
            self.logger.debug(f"Keycloak Admin API response: {response.status_code}")

        if response.status_code != 201:
            raise ActionException(
                f"Keycloak user creation failed: {response.status_code} - {response.text}"
            )

        # Extract keycloak_id from Location header (e.g., .../users/<uuid>)
        location = response.headers.get("Location")
        if not location:
            raise ActionException(
                "Keycloak user creation succeeded but no Location header returned"
            )

        keycloak_id = location.split("/")[-1]
        if self.logger:
            self.logger.debug(f"Created Keycloak user with ID: {keycloak_id}")

        return keycloak_id

    def set_password(
        self, keycloak_id: str, password: str, temporary: bool = False
    ) -> None:
        """
        Set user password in Keycloak.

        Args:
            keycloak_id: The Keycloak user ID (UUID)
            password: The new password to set
            temporary: If True, user must change password on next login

        Raises:
            ActionException: If setting the password fails
        """
        response = self._make_request(
            "PUT",
            f"users/{keycloak_id}/reset-password",
            {
                "type": "password",
                "value": password,
                "temporary": temporary,
            },
        )
        if response.status_code != 204:
            raise ActionException(
                f"Keycloak password set failed: {response.status_code} - {response.text}"
            )

    def clear_user_sessions(self, keycloak_id: str) -> None:
        """
        Clear all sessions for a user in Keycloak.

        Args:
            keycloak_id: The Keycloak user ID (UUID)

        Raises:
            ActionException: If clearing sessions fails
        """
        response = self._make_request("POST", f"users/{keycloak_id}/logout")
        # 204 means success, 404 means user not found (which is OK)
        if response.status_code not in (204, 404):
            raise ActionException(
                f"Keycloak session clear failed: {response.status_code} - {response.text}"
            )
