import os
import smtplib
import ssl
import subprocess
from types import TracebackType
from typing import Any, Dict, List, Optional, Type, cast

import pytest
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP, AuthResult, Envelope, LoginPassword, Session

from openslides_backend.action.mixins.send_email_mixin import (
    ConnectionSecurity,
    EmailMixin,
    EmailSettings,
)
from tests.system.action.base import BaseActionTestCase

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


class AiosmtpdConnectionManager:
    def __init__(self, handler: AIOHandler, auth: bool = False) -> None:
        self.handler = handler
        self.auth = auth

    def __enter__(self) -> None:
        auth_kwargs = {}
        if self.auth:
            auth_kwargs = {
                "auth_required": True,
                "authenticator": Authenticator(),
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

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[TracebackType],
    ) -> None:
        self.controller.stop(no_assert=True)


class Authenticator:
    def __init__(self) -> None:
        pass

    def __call__(
        self,
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


class SendMailWithSmtpServer(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "user/2": {
                    "username": "Testuser 2",
                    "first_name": "Jim",
                    "last_name": "Beam",
                    "email": "",
                    "group_$1_ids": [1],
                    "meeting_ids": [1],
                },
            },
        )
        self.sender = "sender@example.com"
        self.password = "secret"
        self.receivers = ["receiver1@example.com", "receiver2@example.com"]
        EmailSettings.host = "127.0.0.1"
        EmailSettings.timeout = 5
        EmailSettings.user = ""  # important to reset these settings
        EmailSettings.password = ""

    # send tests with different connection_securities without authorization
    def test_send_ssl_tls(self) -> None:
        EmailSettings.connection_security = "SSL/TLS"
        EmailSettings.accept_self_signed_certificate = True
        EmailSettings.port = 465

        handler = AIOHandler()
        with AiosmtpdConnectionManager(handler):
            with EmailMixin.get_mail_connection() as mail_client:
                EmailMixin.send_email(
                    mail_client,
                    self.sender,
                    self.receivers,
                    subject="Test-email",
                    content="Hi\r\nThis is some plain text content!",
                    html=False,
                )
        self.assertEqual("250 Message accepted for delivery", handler.ret_status)
        self.assertEqual(len(handler.emails), 1)
        self.assertEqual(handler.emails[0]["from"], self.sender)
        self.assertEqual(handler.emails[0]["to"], self.receivers)
        self.assertIn(
            "Hi\r\nThis is some plain text content!", handler.emails[0]["data"]
        )

    def test_send_starttls(self) -> None:
        EmailSettings.connection_security = "STARTTLS"
        EmailSettings.accept_self_signed_certificate = True
        EmailSettings.port = 587

        handler = AIOHandler()
        with AiosmtpdConnectionManager(handler):
            with EmailMixin.get_mail_connection() as mail_client:
                response = EmailMixin.send_email(
                    mail_client,
                    self.sender,
                    self.receivers,
                    subject="Test-email",
                    content="Hi\r\nThis is some plain text content!",
                    html=False,
                )
                self.assertEqual(len(response), 0)
        self.assertEqual("250 Message accepted for delivery", handler.ret_status)
        self.assertEqual(len(handler.emails), 1)
        self.assertEqual(handler.emails[0]["from"], self.sender)
        self.assertEqual(handler.emails[0]["to"], self.receivers)
        self.assertIn(
            "Hi\r\nThis is some plain text content!", handler.emails[0]["data"]
        )

    def test_send_no_encryption(self) -> None:
        EmailSettings.connection_security = "NONE"
        EmailSettings.port = 25

        handler = AIOHandler()
        with AiosmtpdConnectionManager(handler):
            with EmailMixin.get_mail_connection() as mail_client:
                response = EmailMixin.send_email(
                    mail_client,
                    self.sender,
                    self.receivers,
                    subject="Test-email",
                    content="Hi\r\nThis is some plain text content!",
                    html=False,
                )
                self.assertEqual(len(response), 0)

        self.assertEqual("250 Message accepted for delivery", handler.ret_status)
        self.assertEqual(len(handler.emails), 1)
        self.assertEqual(handler.emails[0]["from"], self.sender)
        self.assertEqual(handler.emails[0]["to"], self.receivers)
        self.assertIn(
            "Hi\r\nThis is some plain text content!", handler.emails[0]["data"]
        )

    # authentification tests with different connection_securities
    def test_authentication_ssl_tls(self) -> None:
        EmailSettings.connection_security = "SSL/TLS"
        EmailSettings.accept_self_signed_certificate = True
        EmailSettings.port = 465
        EmailSettings.user = self.sender
        EmailSettings.password = self.password

        handler = AIOHandler()
        with AiosmtpdConnectionManager(handler, auth=True):
            with EmailMixin.get_mail_connection() as mail_client:
                EmailMixin.send_email(
                    mail_client,
                    self.sender,
                    self.receivers,
                    subject="Test-email",
                    content="Hi\r\nThis is some plain text content!",
                    html=False,
                )
        self.assertEqual("250 Message accepted for delivery", handler.ret_status)
        self.assertEqual(len(handler.emails), 1)

    def test_authentication_starttls(self) -> None:
        EmailSettings.connection_security = "STARTTLS"
        EmailSettings.accept_self_signed_certificate = True
        EmailSettings.port = 587
        EmailSettings.user = self.sender
        EmailSettings.password = self.password

        handler = AIOHandler()
        with AiosmtpdConnectionManager(handler, auth=True):
            with EmailMixin.get_mail_connection() as mail_client:
                response = EmailMixin.send_email(
                    mail_client,
                    self.sender,
                    self.receivers,
                    subject="Test-email",
                    content="Hi\r\nThis is some plain text content!",
                    html=False,
                )
                self.assertEqual(len(response), 0)
        self.assertEqual("250 Message accepted for delivery", handler.ret_status)
        self.assertEqual(len(handler.emails), 1)

    def test_authentication_no_encryption(self) -> None:
        EmailSettings.connection_security = "NONE"
        EmailSettings.port = 25
        EmailSettings.user = self.sender
        EmailSettings.password = self.password

        handler = AIOHandler()
        with AiosmtpdConnectionManager(handler, auth=True):
            with EmailMixin.get_mail_connection() as mail_client:
                response = EmailMixin.send_email(
                    mail_client,
                    self.sender,
                    self.receivers,
                    subject="Test-email",
                    content="Hi\r\nThis is some plain text content!",
                    html=False,
                )
                self.assertEqual(len(response), 0)

        self.assertEqual("250 Message accepted for delivery", handler.ret_status)
        self.assertEqual(len(handler.emails), 1)

    def test_authentication_wrong_credentials(self) -> None:
        EmailSettings.connection_security = "NONE"
        EmailSettings.port = 25
        EmailSettings.user = self.sender
        EmailSettings.password = "wrong_secret"

        handler = AIOHandler()
        with AiosmtpdConnectionManager(handler, auth=True):
            with pytest.raises(smtplib.SMTPAuthenticationError) as e:
                with EmailMixin.get_mail_connection():
                    pass

        self.assertEqual(e.value.smtp_code, 535)
        self.assertEqual(
            e.value.smtp_error, b"5.7.8 Authentication credentials invalid"
        )
        self.assertEqual(len(handler.emails), 0)

    def test_authentication_not_authenticated(self) -> None:
        EmailSettings.connection_security = "NONE"
        EmailSettings.port = 25

        handler = AIOHandler()
        with AiosmtpdConnectionManager(handler, auth=True):
            with EmailMixin.get_mail_connection() as mail_client:
                with pytest.raises(smtplib.SMTPSenderRefused) as e:
                    EmailMixin.send_email(
                        mail_client,
                        self.sender,
                        self.receivers,
                        subject="Test-email",
                        content="Hi\r\nThis is some plain text content!",
                        html=False,
                    )

                self.assertEqual(e.value.sender, "sender@example.com")
                self.assertEqual(e.value.smtp_code, 530)
                self.assertEqual(e.value.smtp_error, b"5.7.0 Authentication required")
        self.assertEqual(len(handler.emails), 0)

    # send tests with different html/plain content variations
    def test_send_html_email(self) -> None:
        EmailSettings.connection_security = "NONE"
        EmailSettings.port = 25

        handler = AIOHandler()
        with AiosmtpdConnectionManager(handler):
            with EmailMixin.get_mail_connection() as mail_client:
                response = EmailMixin.send_email(
                    mail_client,
                    self.sender,
                    self.receivers,
                    subject="A mail from intevation-test: html with generated plain",
                    content="""
                    <html>
                    <body>
                        <p>Hello dear customer,<br>
                        really nice to meet <strong>you</strong> in html with a <strong>strong you</strong></p>
                        <p>Besides the HTML there is also an auto-generated plain text version</p>
                    </body>
                    </html>
                    """,
                )
                self.assertEqual(len(response), 0)
        self.assertEqual("250 Message accepted for delivery", handler.ret_status)
        self.assertEqual(len(handler.emails), 1)
        self.assertEqual(handler.emails[0]["from"], self.sender)
        self.assertEqual(handler.emails[0]["to"], self.receivers)
        self.assertIn(
            'Content-Type: text/plain; charset="utf-8"',
            handler.emails[0]["data"],
        )
        self.assertIn(
            'Content-Type: text/html; charset="utf-8"',
            handler.emails[0]["data"],
        )

    def test_send_plain_email(self) -> None:
        EmailSettings.connection_security = "NONE"
        EmailSettings.port = 25

        handler = AIOHandler()
        with AiosmtpdConnectionManager(handler):
            with EmailMixin.get_mail_connection() as mail_client:
                response = EmailMixin.send_email(
                    mail_client,
                    self.sender,
                    self.receivers,
                    subject="Test-email",
                    content="Hi\r\nThis is some plain text content!",
                    html=False,
                )
                self.assertEqual(len(response), 0)
        self.assertEqual("250 Message accepted for delivery", handler.ret_status)
        self.assertEqual(len(handler.emails), 1)
        self.assertEqual(handler.emails[0]["from"], self.sender)
        self.assertEqual(handler.emails[0]["to"], self.receivers)
        self.assertIn(
            'Content-Type: text/plain; charset="utf-8"',
            handler.emails[0]["data"],
        )
        self.assertNotIn(
            'Content-Type: text/html; charset="utf-8"',
            handler.emails[0]["data"],
        )

    # miscellanous tests
    def test_self_signed_not_accepted(self) -> None:
        EmailSettings.connection_security = "STARTTLS"
        EmailSettings.accept_self_signed_certificate = False
        EmailSettings.port = 587

        with AiosmtpdConnectionManager(AIOHandler()):
            with pytest.raises(
                ssl.SSLCertVerificationError,
                match="certificate verify failed: self signed certificate",
            ):
                EmailMixin.get_mail_connection().__enter__()

    def test_invalid_receiver_all(self) -> None:
        """Exception is only thrown, if ALL recipients are invalid"""
        EmailSettings.connection_security = "NONE"
        EmailSettings.port = 25

        handler = AIOHandler()
        with AiosmtpdConnectionManager(handler):
            with EmailMixin.get_mail_connection() as mail_client:
                with pytest.raises(smtplib.SMTPRecipientsRefused) as e:
                    EmailMixin.send_email(
                        mail_client,
                        self.sender,
                        "invalidQexample1.com",
                        subject="A mail from intevation-test: plain text",
                        content="Hi you\r\nThis is a nice content line with only plain text!",
                        html=False,
                    )
                self.assertEqual(
                    e.value.recipients,
                    {"invalidQexample1.com": (550, b"invalid eMail address")},
                )
        self.assertEqual("550 invalid eMail address", handler.ret_status)
        self.assertEqual(len(handler.emails), 0)

    def test_invalid_receiver_some(self) -> None:
        """Mail sent, invalid recipients in response"""
        EmailSettings.connection_security = "NONE"
        EmailSettings.port = 25

        handler = AIOHandler()
        with AiosmtpdConnectionManager(handler):
            with EmailMixin.get_mail_connection() as mail_client:
                receivers = self.receivers + ["invalidQexample1.com"]
                response = EmailMixin.send_email(
                    mail_client,
                    self.sender,
                    receivers,
                    subject="A mail from intevation-test: plain text",
                    content="Hi you\r\nThis is a nice content line with only plain text!",
                    html=False,
                )
        self.assertEqual(
            response.get("invalidQexample1.com", tuple()),
            (550, b"invalid eMail address"),
        )
        self.assertEqual("250 Message accepted for delivery", handler.ret_status)
        self.assertEqual(len(handler.emails), 1)
        self.assertEqual(handler.emails[0]["from"], self.sender)
        self.assertEqual(handler.emails[0]["to"], self.receivers)
        self.assertNotEqual(handler.emails[0]["to"], receivers)


class CheckValidEmailAddress(BaseActionTestCase):
    def test_check_valid_emails(self) -> None:
        emails = (
            "anK.Mäk.itraÖi326@gm-ail.com",
            "anK.MäÄk.itraÖi326@gm-.ail.com",
            "anK.MäÄk.itraÖi326@gmÖail.com",
            "anK.MäÄk.itraÖi326@gmail.cÖom",
        )

        for email in emails:
            self.assertTrue(
                EmailMixin.check_email(email), "Email-address {} recognized as False"
            )

    def test_check_invalid_emails(self) -> None:
        emails = (
            "anK.Mä@k.itraÖi326@gm-ail.com",
            "anK.Mä%k.itraÖi326@gm-ail.com",
        )

        for email in emails:
            self.assertFalse(
                EmailMixin.check_email(email), "Email-address {} recognized as True"
            )
