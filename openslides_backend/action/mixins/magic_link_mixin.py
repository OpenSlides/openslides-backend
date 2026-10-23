## Eventually will send magic link invites to users
import os
import hashlib
import secrets
import smtplib
import logging
import requests
from datetime import datetime, timezone
from dataclasses import dataclass

from ...shared.interfaces.write_request import WriteRequest
from ...shared.interfaces.event import Event, EventType
from ..action import Action

logger = logging.getLogger(__name__)

@dataclass
class IDPOneTimeSession():
    sessionID: str
    sessionToken: str

class IDPMagicLinkMixin(Action):

    admin_token_path = "/zitadel/bootstrap/admin.pat"

    external_url = os.getenv("IDP_URL_EXTERNAL", "https://localhost:8800")
    external_host = os.getenv("IDP_EXTERNAL_HOST", "localhost:8800")
    idp_route = os.getenv("IDP_URL_INTERNAL", "http://zitadel-api:8080")
    magic_link_expiry_seconds = os.getenv("IDP_MAGIC_LINK_EXPIRY_TIME", "86400")

    _idp_admin_access_token = ""
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
            raise Exception(f"Error reading admin pat file: {e}")

    def allow_otp_email(self, idp_id: str) -> None:
        idp_admin_access_token = self._get_admin_key()
        try:
            response = requests.post(
                f"{self.idp_route}/v2/users/{idp_id}/otp_email",
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                json={},
            )
            if response.status_code != 200 and response.status_code != 409:
                raise Exception(f"{response.status_code} {response.text}")
        except Exception as e:
            raise Exception(f"Error creating one time session: {e}")

    def create_magic_link(self, idp_id: str) -> str:
        self.allow_otp_email(idp_id)
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        url = f"{self.external_url}/ui/v2/login/magic/{token}"

        # Link token hash with idp id
        try:
            self.datastore.write(
                WriteRequest(
                    events=[
                        Event(
                            type=EventType.Create,
                            collection="magic_links",
                            fields={
                                "token_hash": token_hash,
                                "idp_id": idp_id,
                                "timestamp": datetime.now(timezone.utc)
                            },
                        )
                    ]
                )
            )
        except Exception as e:
            raise Exception(f"Error writing magic link token to database: {e}")

        self.logger.warning("Create new magic link:")
        self.logger.warning(url)

        return url

    def create_one_time_session(self, idp_id: str, email: str) -> IDPOneTimeSession:
        self.allow_otp_email(idp_id)

        sessionID = ""
        otpEmailCode = ""
        idp_admin_access_token = self._get_admin_key()
        try:
            response = requests.post(
                f"{self.idp_route}/v2/sessions",
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                json={
                    "checks": {
                        "user": {
                            "userId": idp_id
                            }
                        },
                    "challenges": {
                        "otpEmail": {
                            "returnCode": {}
                            }
                        },
                    "lifetime": f"{self.magic_link_expiry_seconds}s",
                },
            )
            sessionID = response.json()["sessionId"]
            otpEmailCode = response.json()["challenges"]["otpEmail"]
        except Exception as e:
            raise Exception(f"Error creating one time session: {e}")

        try:
            response = requests.patch(
                f"{self.idp_route}/v2/sessions/{sessionID}",
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                json={
                    "checks": {
                        "otpEmail": {
                            "code": otpEmailCode
                            }
                        },
                },
            )
            sessionToken = response.json()["sessionToken"]
        except Exception as e:
            raise Exception(f"Error validating one time session: {e}")

        return IDPOneTimeSession(sessionID=sessionID, sessionToken=sessionToken)

    def revoke_magic_link(self, tokenHash: str):
        pass
