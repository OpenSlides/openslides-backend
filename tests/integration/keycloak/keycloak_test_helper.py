"""
Keycloak Admin API test helper for integration tests.

This module provides utilities for interacting with Keycloak in integration tests,
including user management and password verification.
"""

import os
from typing import Any, Optional

import requests


class KeycloakTestHelper:
    """Helper class for Keycloak Admin API operations in tests."""

    def __init__(
        self,
        admin_url: Optional[str] = None,
        admin_username: Optional[str] = None,
        admin_password: Optional[str] = None,
        realm: Optional[str] = None,
    ):
        self.admin_url = admin_url or os.environ.get(
            "KEYCLOAK_ADMIN_URL", "http://localhost:8180/auth/admin/realms/openslides"
        )
        self.admin_username = admin_username or os.environ.get(
            "KEYCLOAK_ADMIN_USERNAME", "admin"
        )
        self.admin_password = admin_password or os.environ.get(
            "KEYCLOAK_ADMIN_PASSWORD", "admin"
        )
        self.realm = realm or os.environ.get("KEYCLOAK_REALM", "openslides")
        self._token: Optional[str] = None
        self._token_url = self._derive_token_url()

    def _derive_token_url(self) -> str:
        """Derive the token URL from the admin URL."""
        # admin_url is like: http://localhost:8180/auth/admin/realms/openslides
        # token_url should be: http://localhost:8180/auth/realms/master/protocol/openid-connect/token
        base_url = self.admin_url.split("/admin/")[0]
        return f"{base_url}/realms/master/protocol/openid-connect/token"

    def _get_admin_token(self) -> str:
        """Get admin access token from Keycloak."""
        if self._token:
            return self._token

        response = requests.post(
            self._token_url,
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": self.admin_username,
                "password": self.admin_password,
            },
            timeout=10,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to get Keycloak admin token: {response.status_code} - {response.text}"
            )

        self._token = response.json()["access_token"]
        return self._token

    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[dict[str, Any]] = None,
        return_response: bool = False,
    ) -> Any:
        """Make authenticated request to Keycloak Admin API."""
        token = self._get_admin_token()
        url = f"{self.admin_url}/{endpoint}"

        response = requests.request(
            method,
            url,
            json=json_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if return_response:
            return response

        if response.status_code >= 400:
            raise RuntimeError(
                f"Keycloak API error: {method} {endpoint} - "
                f"{response.status_code}: {response.text}"
            )

        if response.text:
            return response.json()
        return None

    def get_user_by_username(self, username: str) -> Optional[dict[str, Any]]:
        """Fetch user from Keycloak by username."""
        users = self._make_request(
            "GET", f"users?username={username}&exact=true"
        )
        return users[0] if users else None

    def get_user_by_id(self, keycloak_id: str) -> Optional[dict[str, Any]]:
        """Fetch user from Keycloak by ID."""
        try:
            return self._make_request("GET", f"users/{keycloak_id}")
        except RuntimeError:
            return None

    def user_exists(self, keycloak_id: str) -> bool:
        """Check if a user exists in Keycloak."""
        return self.get_user_by_id(keycloak_id) is not None

    def verify_user_password(self, username: str, password: str) -> bool:
        """
        Verify user can authenticate with given password.

        Uses the direct access grant (resource owner password credentials)
        to test authentication.
        """
        # Get token URL for the realm
        base_url = self.admin_url.split("/admin/")[0]
        token_url = f"{base_url}/realms/{self.realm}/protocol/openid-connect/token"

        response = requests.post(
            token_url,
            data={
                "grant_type": "password",
                "client_id": "openslides-client",
                "username": username,
                "password": password,
            },
            timeout=10,
        )

        return response.status_code == 200

    def delete_user(self, keycloak_id: str) -> None:
        """Delete a user from Keycloak."""
        self._make_request("DELETE", f"users/{keycloak_id}")

    def delete_user_by_username(self, username: str) -> bool:
        """Delete a user from Keycloak by username. Returns True if deleted."""
        user = self.get_user_by_username(username)
        if user:
            self.delete_user(user["id"])
            return True
        return False

    def cleanup_test_users(self, prefix: str) -> int:
        """Delete all users with username starting with prefix. Returns count."""
        users = self._make_request("GET", f"users?max=1000")
        deleted = 0
        for user in users:
            if user.get("username", "").startswith(prefix):
                try:
                    self.delete_user(user["id"])
                    deleted += 1
                except RuntimeError:
                    pass
        return deleted

    def create_user(
        self,
        username: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        enabled: bool = True,
        password: Optional[str] = None,
    ) -> str:
        """Create a user in Keycloak and return the keycloak_id."""
        user_data = {
            "username": username,
            "enabled": enabled,
            "requiredActions": [],
        }
        if email:
            user_data["email"] = email
        if first_name:
            user_data["firstName"] = first_name
        if last_name:
            user_data["lastName"] = last_name

        response = self._make_request(
            "POST", "users", user_data, return_response=True
        )

        if response.status_code != 201:
            raise RuntimeError(
                f"Failed to create Keycloak user: {response.status_code} - {response.text}"
            )

        location = response.headers.get("Location")
        if not location:
            raise RuntimeError("No Location header in Keycloak response")

        keycloak_id = location.split("/")[-1]

        if password:
            self.set_user_password(keycloak_id, password)

        return keycloak_id

    def set_user_password(
        self, keycloak_id: str, password: str, temporary: bool = False
    ) -> None:
        """Set password for a Keycloak user."""
        self._make_request(
            "PUT",
            f"users/{keycloak_id}/reset-password",
            {
                "type": "password",
                "value": password,
                "temporary": temporary,
            },
        )
