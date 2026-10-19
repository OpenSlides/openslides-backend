import os
from typing import Any

import jwt
import requests
from argon2 import PasswordHasher
from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)

from ...shared.env import Environment
from ...shared.exceptions import AuthenticationException
from ...shared.interfaces.logging import LoggingModule
from ..database.commands import GetManyRequest
from ..shared.authenticated_service import AuthenticatedService
from .interface import AuthenticationService


class IDPPayload:
    def __init__(self, claims: dict):
        self.sub = claims.get("sub", "")  # User ID
        self.sid = claims.get("sid", "")  # Session ID
        self.os_id = claims.get("os_id", "")  # OS User ID


class AuthenticationOIDC(AuthenticationService, AuthenticatedService):
    """
    OIDC authentication service
    """

    admin_token_path = "/zitadel/bootstrap/admin.pat"
    project_id_path = "/zitadel/bootstrap/project-id"
    client_id_path = "/zitadel/bootstrap/client-id"

    password_hasher = PasswordHasher()
    ANONYMOUS_USER = 0

    external_host = os.getenv("IDP_EXTERNAL_HOST", "localhost:8800")
    idp_route = os.getenv("IDP_URL_INTERNAL", "http://zitadel-api:8080")
    zitadel_enabled = os.getenv("IDP_ENABLE_ZITADEL", "true")
    manual_client_id = os.getenv("IDP_MANUAL_CLIENT_ID", "")

    _idp_admin_access_token = ""
    _idp_project_id = ""
    _idp_client_id = ""

    def __init__(self, env: Environment, logging: LoggingModule) -> None:
        self.logger = logging.getLogger(__name__)
        self.env = env
        self.issuer_url = self.env.IDP_URL_EXTERNAL

        # Set backchannel logout uri
        self._set_backchannel_logout_uri(
            "http://backend:9002/system/action/backchannel_logout"
        )
        with get_new_os_conn() as conn:
            self.datastore = ExtendedDatabase(conn, logging, env)

    def _get_admin_key(self) -> str:
        if not self.zitadel_enabled:
            return ""

        if self._idp_admin_access_token != "":
            return self._idp_admin_access_token

        # Fetch key from admin file
        try:
            with open(self.admin_token_path) as file:
                self._idp_admin_access_token = file.read().replace("\n", "")
                return self._idp_admin_access_token
        except Exception as e:
            raise AuthenticationException(f"Error reading admin pat file: {e}")

    def _get_project_id(self) -> str:
        if not self.zitadel_enabled:
            return ""

        if self._idp_project_id != "":
            return self._idp_project_id

        # Fetch key from project id file
        try:
            with open(self.project_id_path) as file:
                self._idp_project_id = file.read().replace("\n", "")
                return self._idp_project_id
        except Exception as e:
            raise AuthenticationException(f"Error reading project id file: {e}")

    def _get_client_id(self) -> str:
        if self.manual_client_id is not "":
            return self.manual_client_id

        if self._idp_client_id != "":
            return self._idp_client_id

        # Fetch key from client id file
        try:
            with open(self.client_id_path) as file:
                self._idp_client_id = file.read().replace("\n", "")
                return self._idp_client_id
        except Exception as e:
            raise AuthenticationException(f"Error reading client id file: {e}")

    def _set_backchannel_logout_uri(self, uri: str) -> None:
        if not self.zitadel_enabled:
            self.logger.info("Zitadel is not enabled. Skip setting backchannel logout URI")
            return

        # Sets backchannel logout uri in the idp service
        idp_admin_access_token = self._get_admin_key()
        idp_project_id = self._get_project_id()

        try:
            # Update URI
            response = requests.post(
                f"{self.idp_route}/zitadel.application.v2.ApplicationService/UpdateApplication",
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                json={
                    "applicationId": "OpenSlides",
                    "projectId": f"{idp_project_id}",
                    "oidcConfiguration": {"backChannelLogoutUri": f"{uri}"},
                },
            )

            if response.status_code != 200:
                if "COMMAND-1m88i" in response.text:
                    self.logger.warning(
                        "Tried to set backchannel logout URI, but the given URI is already configured in Zitadel"
                    )
                    return
                raise AuthenticationException(f"{response.status_code}: {response.text}")
        except Exception as e:
            raise AuthenticationException(f"Error setting backchannel logout URI: {e}")

    def authenticate(self) -> tuple[int, str | None]:
        self.logger.debug("Authentication request received")

        # Fetch JWT
        header_value = self.access_token
        if not header_value.startswith("Bearer: "):
            raise AuthenticationException("Authorization does not contain 'Bearer:'")

        # Convert JWT to Payload
        token_string = header_value[len("Bearer: ") :]
        payload = IDPPayload(self._extract_claims(token_string))

        if not payload.sub or not payload.os_id:
            return (0, "")

        if self.is_session_id_blocked(payload.sid):
            self.logger.warning(f"Session ID {payload.sid} is blocked by blocklist")
            return (0, "")

        return (int(payload.os_id), header_value)

    def decode_logout_token(self, encoded_logout_token: str) -> str:
        # Extract session ID
        claims = self._extract_claims(encoded_logout_token)

        # Required per OIDC backchannel logout: events must include the backchannel logout event
        backchannel_event_key = "http://schemas.openid.net/event/backchannel-logout"
        events = claims.get("events")
        if not isinstance(events, dict) or backchannel_event_key not in events:
            raise AuthenticationException(
                "Token is not a valid backchannel logout token (missing events)"
            )

        # Validate issuer
        if claims.get("iss") != self.issuer_url:
            raise AuthenticationException(
                f"Invalid issuer: got {claims.get('iss')}, want {self.issuer_url}"
            )

        # Extract session ID
        if not claims.get("sid"):
            raise AuthenticationException("Logout token does not contain session ID")
        elif not isinstance(claims.get("sid"), str):
            raise AuthenticationException("Logout token has no valid session ID")

        return claims["sid"]

    def _extract_claims(self, token: str) -> dict[str, Any]:
        try:
            claims = jwt.decode(
                token,
                algorithms=["RS256"],
                audience=self._get_client_id(),
                options={"verify_aud": True, "verify_signature": False},
            )
        except jwt.exceptions.DecodeError as e:
            raise AuthenticationException(f"Decoding JWT token: {e}")
        except jwt.exceptions.InvalidAudienceError as e:
            raise AuthenticationException(f"Audience check on JWT token: {e}")

        return claims

    def hash(self, to_hash: str) -> str:
        return self.password_hasher.hash(to_hash)

    def is_equal(self, to_hash: str, to_compare: str) -> bool:
        return to_hash == to_compare

    def is_anonymous(self, user_id: int) -> bool:
        return user_id == self.ANONYMOUS_USER

