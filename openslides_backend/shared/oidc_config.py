"""
OIDC Configuration Module

Provides OIDC configuration exclusively via environment variables,
replacing the database-backed organization settings.
"""

import json
import os
from dataclasses import dataclass

from .env import is_truthy


@dataclass
class OidcConfig:
    """OIDC configuration loaded from environment variables."""

    enabled: bool
    provider_url: str
    internal_provider_url: str
    client_id: str
    client_secret: str
    login_button_text: str
    admin_api_enabled: bool
    admin_api_url: str
    admin_client_id: str  # Client ID for admin API (needs service account)
    admin_client_secret: str  # Client secret for admin API
    attr_mapping: dict

    @classmethod
    def from_env(cls) -> "OidcConfig":
        """Load OIDC configuration from environment variables."""
        mapping_str = os.environ.get("OIDC_ATTR_MAPPING", "{}")
        try:
            attr_mapping = json.loads(mapping_str)
        except json.JSONDecodeError:
            attr_mapping = {}

        # For admin API, use dedicated admin credentials if provided,
        # otherwise fall back to the regular client credentials
        client_id = os.environ.get("OIDC_CLIENT_ID", "")
        client_secret = os.environ.get("OIDC_CLIENT_SECRET", "")

        return cls(
            enabled=is_truthy(os.environ.get("OIDC_ENABLED", "false")),
            provider_url=os.environ.get("OIDC_PROVIDER_URL", ""),
            internal_provider_url=os.environ.get("OIDC_INTERNAL_PROVIDER_URL", ""),
            client_id=client_id,
            client_secret=client_secret,
            login_button_text=os.environ.get("OIDC_LOGIN_BUTTON_TEXT", "OIDC login"),
            admin_api_enabled=is_truthy(
                os.environ.get("OIDC_ADMIN_API_ENABLED", "false")
            ),
            admin_api_url=os.environ.get("OIDC_ADMIN_API_URL", ""),
            admin_client_id=os.environ.get("OIDC_ADMIN_CLIENT_ID", client_id),
            admin_client_secret=os.environ.get("OIDC_ADMIN_CLIENT_SECRET", client_secret),
            attr_mapping=attr_mapping,
        )


_config: OidcConfig | None = None


def get_oidc_config() -> OidcConfig:
    """
    Get the OIDC configuration singleton.

    The configuration is loaded once from environment variables
    and cached for subsequent calls.
    """
    global _config
    if _config is None:
        _config = OidcConfig.from_env()
    return _config


def reset_oidc_config() -> None:
    """
    Reset the OIDC configuration singleton.

    Useful for testing purposes to reload configuration.
    """
    global _config
    _config = None
