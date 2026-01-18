"""
OIDC Who Am I Presenter

Validates an OIDC access token from Keycloak, provisions the user if needed,
and returns the OpenSlides user ID.
"""

import os
from base64 import b64encode
from typing import Any

import fastjsonschema
import requests

from ..shared.env import DEV_PASSWORD
from ..shared.exceptions import PresenterException
from ..shared.filters import FilterOperator
from ..shared.oidc_validator import OidcTokenValidator
from ..shared.schema import schema_version
from ..shared.util import ONE_ORGANIZATION_FQID
from .base import BasePresenter
from .presenter import register_presenter

oidc_who_am_i_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "oidc_who_am_i",
        "description": "Validate OIDC token and return user info",
        "properties": {
            "access_token": {
                "type": "string",
                "description": "The OIDC access token from Keycloak",
                "minLength": 1,
            },
        },
        "required": ["access_token"],
        "additionalProperties": False,
    }
)


@register_presenter("oidc_who_am_i")
class OidcWhoAmI(BasePresenter):
    """
    OIDC who-am-i presenter.

    1. Validates the OIDC access token (RS256 via JWKS)
    2. Fetches user info from Keycloak userinfo endpoint
    3. Searches for existing user by keycloak_id
    4. Provisions user if not found (via internal action call)
    5. Returns user ID and relevant info
    """

    schema = oidc_who_am_i_schema

    def get_result(self) -> dict[str, Any]:
        access_token = self.data["access_token"]

        # 1. Load OIDC config from organization
        organization = self.datastore.get(
            ONE_ORGANIZATION_FQID,
            [
                "oidc_enabled",
                "oidc_provider_url",
                "oidc_client_id",
                "oidc_client_secret",
            ],
            lock_result=False,
        )

        if not organization.get("oidc_enabled"):
            raise PresenterException(
                "OIDC authentication is not enabled in OpenSlides configuration"
            )

        provider_url = organization.get("oidc_provider_url")
        client_id = organization.get("oidc_client_id")

        if not provider_url or not client_id:
            raise PresenterException("OIDC provider URL or client ID not configured")

        # 2. Validate token and extract keycloak_id (sub claim)
        validator = OidcTokenValidator(
            provider_url=provider_url,
            client_id=client_id,
            client_secret=organization.get("oidc_client_secret"),
        )

        try:
            token_payload = validator.validate_token(access_token)
            keycloak_id = token_payload.get("sub")
        except PresenterException:
            raise
        except Exception as e:
            raise PresenterException(f"Token validation failed: {e}")

        if not keycloak_id:
            raise PresenterException("Missing 'sub' claim in token")

        # 3. Get user info from Keycloak
        try:
            user_info = validator.get_user_info(access_token)
        except PresenterException:
            raise
        except Exception as e:
            raise PresenterException(f"Failed to fetch user info: {e}")

        # 4. Search for existing user by keycloak_id
        users = self.datastore.filter(
            "user",
            FilterOperator("keycloak_id", "=", keycloak_id),
            ["id", "username", "first_name", "last_name", "email", "is_active"],
        )

        if len(users) == 1:
            # User exists
            user = next(iter(users.values()))
            if not user.get("is_active", True):
                raise PresenterException("User account is deactivated")

            return {
                "user_id": user["id"],
                "keycloak_id": keycloak_id,
                "username": user.get("username"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "email": user.get("email"),
                "provisioned": False,
            }

        elif len(users) > 1:
            raise PresenterException(
                f"Multiple users found with keycloak_id {keycloak_id}"
            )

        # 5. User doesn't exist - provision via internal action
        user_id = self._provision_user(keycloak_id, user_info)

        # Fetch the created user's info
        users = self.datastore.filter(
            "user",
            FilterOperator("keycloak_id", "=", keycloak_id),
            ["id", "username", "first_name", "last_name", "email"],
        )

        if users:
            user = next(iter(users.values()))
            return {
                "user_id": user["id"],
                "keycloak_id": keycloak_id,
                "username": user.get("username"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "email": user.get("email"),
                "provisioned": True,
            }
        else:
            return {
                "user_id": user_id,
                "keycloak_id": keycloak_id,
                "provisioned": True,
            }

    def _provision_user(
        self, keycloak_id: str, user_info: dict[str, Any]
    ) -> int | None:
        """
        Provision a new user via the internal save_keycloak_account action.
        """
        # Prepare the action data from user_info
        action_data = {
            "keycloak_id": keycloak_id,
            "email": user_info.get("email"),
            "given_name": user_info.get("given_name"),
            "family_name": user_info.get("family_name"),
            "preferred_username": user_info.get("preferred_username"),
            "name": user_info.get("name"),
        }

        # Remove None values
        action_data = {k: v for k, v in action_data.items() if v is not None}

        # Get internal auth password
        internal_password = self._get_internal_auth_password()

        # Make internal HTTP request to the action endpoint
        try:
            # Get the action port from environment
            action_port = os.environ.get("ACTION_PORT", "9002")
            action_url = f"http://localhost:{action_port}/internal/action/handle_request"

            response = requests.post(
                action_url,
                json=[
                    {
                        "action": "user.save_keycloak_account",
                        "data": [action_data],
                    }
                ],
                headers={
                    "Authorization": b64encode(internal_password.encode()).decode(),
                    "Content-Type": "application/json",
                },
                timeout=10,
            )

            if response.status_code != 200:
                self.logger.error(
                    f"Failed to provision user: HTTP {response.status_code} - {response.text}"
                )
                raise PresenterException(
                    f"Failed to provision user: HTTP {response.status_code}"
                )

            result = response.json()
            if result.get("success") and result.get("results"):
                action_results = result["results"]
                if action_results and action_results[0]:
                    return action_results[0][0].get("user_id")

            return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to call internal action: {e}")
            raise PresenterException(f"Failed to provision user: {e}")

    def _get_internal_auth_password(self) -> str:
        """Get the internal authentication password."""
        # Check for password file first
        password_file = os.environ.get("INTERNAL_AUTH_PASSWORD_FILE")
        if password_file and os.path.exists(password_file):
            with open(password_file) as f:
                return f.read().strip()

        # In dev mode, use the dev password
        if os.environ.get("OPENSLIDES_DEVELOPMENT", "").lower() in (
            "1",
            "on",
            "true",
        ):
            return DEV_PASSWORD

        raise PresenterException("Internal authentication not configured")
