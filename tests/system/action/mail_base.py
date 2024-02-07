import os
import ssl
import subprocess
from types import TracebackType
from typing import Any, cast

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP, AuthResult, Envelope, LoginPassword, Session

from openslides_backend.action.mixins.send_email_mixin import (
    ConnectionSecurity,
    EmailSettings,
    EmailUtils,
)

# Create certificate if they don't exist
if not os.path.exists("key.pem") or not os.path.exists("cert.pem"):
    subprocess.call(
        "openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=localhost'",
        shell=True,
    )


class AIOHandler:
    def __init__(self) -> None:
        self.emails: list[dict[str, Any]] = []
        self.ret_status = "unset"

    async def handle_RCPT(
        self,
        server: SMTP,
        session: Session,
        envelope: Envelope,
        address: str,
        rcpt_options: list[Any],
    ) -> Any:
        if not EmailUtils.check_email(address):
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

        if EmailSettings.connection_security == ConnectionSecurity.SSLTLS:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_default_certs(purpose=ssl.Purpose.SERVER_AUTH)
            ssl_context.load_cert_chain("cert.pem", "key.pem")

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
        elif EmailSettings.connection_security == ConnectionSecurity.STARTTLS:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_default_certs(purpose=ssl.Purpose.SERVER_AUTH)
            ssl_context.load_cert_chain("cert.pem", "key.pem")
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
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_traceback: TracebackType | None,
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


def set_test_email_settings() -> None:
    EmailSettings.connection_security = ConnectionSecurity.NONE
    EmailSettings.host = "127.0.0.1"
    EmailSettings.port = 25
    EmailSettings.timeout = 5
    EmailSettings.user = ""
    EmailSettings.password = ""
    EmailSettings.accept_self_signed_certificate = False
    EmailSettings.default_from_email = "noreply@example.com"
