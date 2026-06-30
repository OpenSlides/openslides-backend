from urllib import parse

import os
import time
import base64
import requests
import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from argon2 import PasswordHasher

from ...shared.filters import FilterOperator
from ...shared.exceptions import AuthenticationException
from ...shared.interfaces.logging import LoggingModule
from ...shared.env import Environment
from ..shared.authenticated_service import AuthenticatedService
from .interface import AuthenticationService

class IDPPayload:
    def __init__(self, claims: dict):
        self.sub = claims.get("sub", "")                               # User ID
        self.sid = claims.get("sid", "")                               # Session ID
        self.os_id = claims.get("os_id", "")                           # OS User ID
        self.preferred_username = claims.get("preferred_username", "") # User Name
        self.azp = claims.get("azp", "")                               # Client name
        self.exp = claims.get("exp", 0)                                # Expirery Date
        self.iss = claims.get("iss", "")                               # Issuer URL

class AuthenticationOIDC(AuthenticationService, AuthenticatedService):
    """
    OIDC authentication service
    """

    passwordHasher = PasswordHasher()
    ANONYMOUS_USER = 0

    def __init__(self, env: Environment, logging: LoggingModule) -> None:
        self.logger = logging.getLogger(__name__)
        self.env = env
        self.issuer_url = self.env.OIDC_ISSUER_URL_DOCKER
        self.headers = {"Content-Type": "application/json"}

        # JWT public key caching
        self._keys: dict = {}
        self._keys_expires_at: float = 0.0

        if self.issuer_url is None or self.issuer_url == "":
            self.issuer_url = self.env.OIDC_ISSUER_URL

    def authenticate(self) -> tuple[int, str | None]:
        self.logger.debug(
            f"Start request to authentication service with the following data: access_token: {self.access_token}"
        )

        # Fetch JWT
        header_value = self.access_token
        if not header_value.startswith("Bearer: "):
            raise AuthenticationException(f"Authorization does not contain 'Bearer:', instead {self.access_token}")

        # Convert JWT to Payload
        payload = self._extract_payload(header_value[len("Bearer: "):])

        if not payload or not payload.sub or not payload.os_id:
            return (0, "")

        return (int(payload.os_id), header_value)

    def _extract_payload(self, token_string: str) -> IDPPayload:
        try:
            unverified_header = jwt.get_unverified_header(token_string)
        except jwt.exceptions.DecodeError as e:
            raise AuthenticationException(f"Parsing JWT token header: {e}")

        kid = unverified_header.get("kid")
        if not kid:
            raise AuthenticationException("No IDP id in auth headers")

        public_key = self._get_key(kid)

        try:
            claims = jwt.decode(
                token_string,
                public_key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
        except jwt.exceptions.ExpiredSignatureError as e:
            raise AuthenticationException(f"JWT token expired: {e}")
        except jwt.exceptions.InvalidTokenError as e:
            raise AuthenticationException(f"Validating JWT token: {e}")

        return IDPPayload(claims)

    def _get_key(self, kid: str):
        if kid in self._keys and time.time() < self._keys_expires_at:
            return self._keys[kid]
        return self._fetch_jwks(kid)

    def _fetch_jwks(self, kid: str):
        url = f"{self.issuer_url}/protocol/openid-connect/certs"
        try:
            resp = requests.get(url, timeout=10)
        except requests.RequestException as e:
            raise AuthenticationException(f"Fetching JWKS: {e}")

        if resp.status_code != 200:
            raise AuthenticationException(f"JWKS request failed: {resp.status_code}")

        self._keys = {}
        for key in resp.json().get("keys", []):
            if key.get("kty") != "RSA":
                continue
            try:
                self._keys[key["kid"]] = self._parse_rsa_public_key(key["n"], key["e"])
            except Exception:
                continue

        self._keys_expires_at = time.time() + 3600

        if kid not in self._keys:
            raise AuthenticationException(f"Key {kid} not found in JWKS")

        return self._keys[kid]

    @staticmethod
    def _parse_rsa_public_key(n_str: str, e_str: str):
        def b64url_to_int(s: str) -> int:
            padded = s + "=" * (-len(s) % 4)
            return int.from_bytes(base64.urlsafe_b64decode(padded), "big")

        return RSAPublicNumbers(b64url_to_int(e_str), b64url_to_int(n_str)).public_key()


    def hash(self, toHash: str) -> str:
        return self.passwordHasher.hash(toHash)

    def is_equal(self, toHash: str, toCompare: str) -> bool:
        return toHash == toCompare


    def is_anonymous(self, user_id: int) -> bool:
        return user_id == self.ANONYMOUS_USER

    def clear_all_sessions(self) -> None:
        self.auth_handler.clear_all_sessions(
            self.access_token
        )

    def clear_sessions_by_user_id(self, user_id: int) -> None:
        self.auth_handler.clear_sessions_by_user_id(user_id)
