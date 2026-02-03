"""
OIDC Token Validator

Validates RS256 signed JWT tokens from Keycloak/OIDC providers and fetches user info.
"""

from typing import Any

import jwt
import requests
from jwt import PyJWKClient

from .exceptions import PresenterException


class OidcTokenValidator:
    """
    OIDC Token Validator for RS256 signed tokens.

    Validates tokens from Keycloak/OIDC providers using JWKS and fetches user info.
    """

    def __init__(
        self,
        provider_url: str,
        client_id: str,
        client_secret: str | None = None,
    ):
        """
        Initialize the OIDC validator.

        Args:
            provider_url: Keycloak realm URL (e.g. https://keycloak/realms/openslides)
            client_id: OIDC client ID
            client_secret: OIDC client secret (optional, for confidential clients)
        """
        self.issuer = provider_url
        self.audience = client_id
        self.client_secret = client_secret
        self.jwks_uri = f"{provider_url}/protocol/openid-connect/certs"
        self.userinfo_uri = f"{provider_url}/protocol/openid-connect/userinfo"
        self._jwks_client: PyJWKClient | None = None

    @property
    def jwks_client(self) -> PyJWKClient:
        """Lazy-load JWKS client."""
        if self._jwks_client is None:
            self._jwks_client = PyJWKClient(self.jwks_uri)
        return self._jwks_client

    def validate_token(self, token: str) -> dict[str, Any]:
        """
        Validate an OIDC access token and return the decoded payload.

        Args:
            token: The JWT token string (without 'bearer ' prefix)

        Returns:
            Decoded token payload

        Raises:
            PresenterException: If token validation fails
        """
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            # Disable PyJWT's audience check because Keycloak access tokens
            # may not include an `aud` claim (they use `azp` instead).
            # We verify the audience/azp manually below.
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False},
                issuer=self.issuer,
            )

            # Manual audience verification: check `azp` first, then `aud`.
            # Keycloak access tokens set `azp` (authorized party) to the
            # requesting client and may set `aud` to other clients (e.g.
            # "account") that have role mappings, so `azp` is the reliable
            # indicator of the intended audience.
            token_azp = payload.get("azp")
            token_aud = payload.get("aud")
            if token_azp:
                if token_azp != self.audience:
                    raise PresenterException("Invalid token audience")
            elif token_aud:
                aud_list = [token_aud] if isinstance(token_aud, str) else token_aud
                if self.audience not in aud_list:
                    raise PresenterException("Invalid token audience")

            return payload
        except PresenterException:
            raise
        except jwt.exceptions.InvalidSignatureError:
            raise PresenterException("Invalid token signature")
        except jwt.exceptions.ExpiredSignatureError:
            raise PresenterException("Token has expired")
        except jwt.exceptions.InvalidIssuerError:
            raise PresenterException("Invalid token issuer")
        except jwt.exceptions.InvalidAudienceError:
            raise PresenterException("Invalid token audience")
        except jwt.exceptions.DecodeError as e:
            raise PresenterException(f"Token decode error: {e}")
        except jwt.exceptions.PyJWKClientError as e:
            raise PresenterException(f"JWKS fetch error: {e}")
        except Exception as e:
            raise PresenterException(f"Token validation failed: {e}")

    def get_user_info(self, token: str) -> dict[str, Any]:
        """
        Fetch user info from the OIDC provider's userinfo endpoint.

        Args:
            token: The JWT access token

        Returns:
            User info from the OIDC provider

        Raises:
            PresenterException: If the request fails
        """
        try:
            response = requests.get(
                self.userinfo_uri,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise PresenterException(f"Failed to fetch user info: {e}")

    def extract_keycloak_id(self, token: str) -> str:
        """
        Validate token and extract the Keycloak user ID (sub claim).

        Args:
            token: The JWT access token

        Returns:
            The 'sub' claim from the token (Keycloak user UUID)

        Raises:
            PresenterException: If token is invalid or missing sub claim
        """
        payload = self.validate_token(token)
        keycloak_id = payload.get("sub")
        if not keycloak_id:
            raise PresenterException("Missing 'sub' claim in token")
        if not isinstance(keycloak_id, str):
            raise PresenterException(
                f"'sub' claim must be a string, got {type(keycloak_id).__name__}"
            )
        return keycloak_id
