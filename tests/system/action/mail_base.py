import os
import ssl
import subprocess
from types import TracebackType
from typing import Any, Dict, List, Optional, Type, cast

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP, AuthResult, Envelope, LoginPassword, Session

from openslides_backend.action.mixins.send_email_mixin import (
    ConnectionSecurity,
    EmailMixin,
    EmailSettings,
)

# Create certificate if they don't exist
if not os.path.exists("key.pem") or not os.path.exists("cert.pem"):
    subprocess.call(
        "openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=localhost'",
        shell=True,
    )


class AIOHandler:
    def __init__(self) -> None:
        self.emails: List[Dict[str, Any]] = []
        self.ret_status = "unset"

    async def handle_RCPT(
        self,
        server: SMTP,
        session: Session,
        envelope: Envelope,
        address: str,
        rcpt_options: List[Any],
    ) -> Any:
        if not EmailMixin.check_email(address):
            self.ret_status = "550 invalid eMail address"
            return self.ret_status
        if "create_error551" in address:
            self.ret_status = "551 invalid eMail address from server"
            return self.ret_status
        envelope.rcpt_tos.append(address)
        self.ret_status = "250 OK"
        return self.ret_status

    async def handle_DATA(
        self, server: SMTP, session: Session, envelope: Envelope
    ) -> Any:
        content = cast(bytes, envelope.content)
        self.emails.append(
            {
                "from": envelope.mail_from,
                "to": envelope.rcpt_tos,
                "data": content.decode("utf8", errors="replace"),
            }
        )
        self.ret_status = "250 Message accepted for delivery"
        return self.ret_status


class AiosmtpdServerManager:
    def __init__(self, handler: AIOHandler, auth: bool = False) -> None:
        self.handler = handler
        self.auth = auth

    def __enter__(self) -> Controller:
        auth_kwargs = {}
        if self.auth:
            auth_kwargs = {
                "auth_required": True,
                "authenticator": authenticator,
            }

        if EmailSettings.connection_security in [
            ConnectionSecurity.STARTTLS,
            ConnectionSecurity.SSLTLS,
        ]:
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context.load_default_certs(purpose=ssl.Purpose.SERVER_AUTH)
            ssl_context.load_cert_chain("cert.pem", "key.pem")
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.VerifyMode.CERT_NONE
            if EmailSettings.connection_security == ConnectionSecurity.SSLTLS:
                # This is a hack: The aiosmtpd library does not issue AUTH in EHLO, if not starttls is used.
                # For other methods (SSL/TLS and NONE) setting auth_require_tls allows AUTH. The intention is to
                # allow AUTH before TLS (which is ok for NONE), but a hack for SSL/TLS since we have an
                # encrypted connection
                if self.auth:
                    auth_kwargs["auth_require_tls"] = False
                self.controller = Controller(
                    self.handler,
                    EmailSettings.host,
                    EmailSettings.port,
                    server_hostname="127.0.0.1",
                    ssl_context=ssl_context,
                    **auth_kwargs,  # type: ignore
                )
            else:
                self.controller = Controller(
                    self.handler,
                    EmailSettings.host,
                    EmailSettings.port,
                    server_hostname="127.0.0.1",
                    require_starttls=True,
                    tls_context=ssl_context,
                    **auth_kwargs,  # type: ignore
                )
        else:
            if self.auth:
                auth_kwargs["auth_require_tls"] = False
            self.controller = Controller(
                self.handler, EmailSettings.host, EmailSettings.port, **auth_kwargs  # type: ignore
            )

        self.controller.start()
        return self.controller

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[TracebackType],
    ) -> None:
        if self.controller.loop.is_running():
            self.controller.stop(no_assert=True)


def authenticator(
    server: SMTP,
    session: Session,
    envelope: Envelope,
    mechanism: str,
    auth_data: LoginPassword,
) -> AuthResult:
    fail_nothandled = AuthResult(success=False, handled=False)
    if mechanism not in ("LOGIN", "PLAIN"):
        return fail_nothandled
    if not isinstance(auth_data, LoginPassword):
        return fail_nothandled

    if auth_data.login == b"sender@example.com" and auth_data.password == b"secret":
        return AuthResult(success=True)
    else:
        return fail_nothandled
