import os
import ssl
import subprocess
from typing import Any, Dict, List

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import AuthResult

from openslides_backend.action.mixins.send_email_mixin import (
    ConSecurity,
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


class AiosmtpdConnectionManager:
    def __init__(self, create: bool = True):
        self.create = create
        self.started = False

    def __enter__(self):
        if not self.create:
            return None
        handler = AIOHandler()
        if EmailSettings.connection_security in [
            ConSecurity.STARTTLS,
            ConSecurity.SSLTLS,
        ]:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain("cert.pem", "key.pem")
            ssl_context.check_hostname = False
            if EmailSettings.connection_security == ConSecurity.SSLTLS:
                ssl_context.verify_mode = ssl.VerifyMode.CERT_NONE
                self.controller = Controller(
                    handler,
                    EmailSettings.host,
                    EmailSettings.port,
                    server_hostname="127.0.0.1",
                    ssl_context=ssl_context,
                    # auth_required=True,
                    # authenticator=authenticator1,
                )
            else:
                self.controller = Controller(
                    handler,
                    EmailSettings.host,
                    EmailSettings.port,
                    server_hostname="127.0.0.1",
                    require_starttls=True,
                    tls_context=ssl_context,
                    # auth_required=True,
                    # authenticator=authenticator1,
                )
        else:
            self.controller = Controller(
                handler, EmailSettings.host, EmailSettings.port
            )

        try:
            self.controller.start()
            self.started = True
        except Exception as e:
            raise e
        return self.controller

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.started:
            self.controller.stop()


class AIOHandler:
    def __init__(self):
        self.emails: List[Dict[str, Any]] = []
        self.ret_status = "unset"

    async def handle_RCPT(
        self, server, session, envelope, address, rcpt_options
    ) -> Any:
        if not EmailMixin.check_email(address):
            self.ret_status = "550 invalid eMail address"
            return self.ret_status
        envelope.rcpt_tos.append(address)
        self.ret_status = "250 OK"
        return self.ret_status

    async def handle_DATA(self, server, session, envelope) -> Any:
        self.emails.append(
            {
                "from": envelope.mail_from,
                "to": envelope.rcpt_tos,
                "data": envelope.content.decode("utf8", errors="replace"),
            }
        )
        self.ret_status = "250 Message accepted for delivery"
        return self.ret_status


def authenticator1(server, session, envelope, mechanism, auth_data) -> AuthResult:
    return AuthResult(True)


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
        self.sender = "sender@intevation.com"
        self.receiver1 = "receiver1@example1.com"
        EmailSettings.host = "127.0.0.1"
        EmailSettings.port = 25
        # EmailSettings.user = self.sender
        # EmailSettings.password = "secret"
        # EMAIL_CONNECTION_SECURITY use NONE, STARTTLS or SSL/TLS
        EmailSettings.connection_security = "NONE"
        EmailSettings.timeout = 5
        EmailSettings.accept_self_signed_certificate = True

    def test_send_correct_plain_ssl(self) -> None:
        EmailSettings.connection_security = "SSL/TLS"
        EmailSettings.port = 465
        try:
            with AiosmtpdConnectionManager() as controller:
                with EmailMixin.get_mail_connection() as mail_client:
                    response = EmailMixin.send_email(
                        mail_client,
                        self.sender,
                        [
                            self.receiver1,
                            "invalidQexample1.com",
                            "receiver2@example2.com",
                        ],
                        subject="A mail from intevation-test: plain text",
                        content="Hi you\r\nThis is a nice content line with only plain text!",
                        html=False,
                    )
        except Exception as e:
            raise Exception(str(e))
        self.assertIn("invalidQexample1.com", list(response.keys())[0])
        if controller and hasattr(controller, "handler") and controller.handler:
            self.assertEqual(
                "250 Message accepted for delivery", controller.handler.ret_status
            )
            self.assertEqual(len(controller.handler.emails), 1)
            self.assertEqual(controller.handler.emails[0]["from"], self.sender)
            self.assertEqual(len(controller.handler.emails[0]["to"]), 2)
            self.assertIn(
                'Content-Type: text/plain; charset="utf-8"',
                controller.handler.emails[0]["data"],
            )
            self.assertNotIn(
                'Content-Type: text/html; charset="utf-8"',
                controller.handler.emails[0]["data"],
            )

    def test_send_correct_html_generated_plain_starttls(self) -> None:
        EmailSettings.connection_security = "STARTTLS"
        EmailSettings.port = 587
        try:
            with AiosmtpdConnectionManager() as controller:
                with EmailMixin.get_mail_connection() as mail_client:
                    response = EmailMixin.send_email(
                        mail_client,
                        self.sender,
                        self.receiver1,
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
        except Exception as e:
            raise Exception(str(e))
        self.assertEqual(len(response), 0)
        if controller and hasattr(controller, "handler") and controller.handler:
            self.assertEqual(
                "250 Message accepted for delivery", controller.handler.ret_status
            )
            self.assertEqual(len(controller.handler.emails), 1)
            self.assertEqual(controller.handler.emails[0]["from"], self.sender)
            self.assertEqual(len(controller.handler.emails[0]["to"]), 1)
            self.assertIn(
                'Content-Type: text/plain; charset="utf-8"',
                controller.handler.emails[0]["data"],
            )
            self.assertIn(
                'Content-Type: text/html; charset="utf-8"',
                controller.handler.emails[0]["data"],
            )

    def test_send_correct_html_without_plain_NONE(self) -> None:
        try:
            with AiosmtpdConnectionManager() as controller:
                with EmailMixin.get_mail_connection() as mail_client:
                    response = EmailMixin.send_email(
                        mail_client,
                        self.sender,
                        [
                            self.receiver1,
                            "receiver2@example2.com",
                        ],
                        "A mail from intevation-test: html only",
                        content="""
                        <html>
                        <body>
                            <p>Hello dear customer,<br>
                            really nice to meet <strong>you</strong></p>
                            <p>HTML only, there is no parallel plain text</p>
                        </body>
                        </html>
                        """,
                        contentplain=None,
                    )
        except Exception as e:
            raise Exception(str(e))
        self.assertEqual(len(response), 0)
        if controller and hasattr(controller, "handler") and controller.handler:
            self.assertEqual(
                "250 Message accepted for delivery", controller.handler.ret_status
            )
            self.assertEqual(len(controller.handler.emails), 1)
            self.assertEqual(controller.handler.emails[0]["from"], self.sender)
            self.assertEqual(len(controller.handler.emails[0]["to"]), 2)
            self.assertNotIn(
                'Content-Type: text/plain; charset="utf-8"',
                controller.handler.emails[0]["data"],
            )
            self.assertIn(
                'Content-Type: text/html; charset="utf-8"',
                controller.handler.emails[0]["data"],
            )


class CheckValidEmailAddress(BaseActionTestCase):
    def test_check_email(self) -> None:
        email = "anK.Mäk.itraÖi326@gm-ail.com"
        self.assertTrue(
            EmailMixin.check_email(email), "Email-address {} recognized as False"
        )

        email = "anK.MäÄk.itraÖi326@gm-.ail.com"
        self.assertTrue(
            EmailMixin.check_email(email), "Email-address {} recognized as False"
        )

        email = "anK.MäÄk.itraÖi326@gmÖail.com"
        self.assertTrue(
            EmailMixin.check_email(email), "Email-address {} recognized as False"
        )

        email = "anK.MäÄk.itraÖi326@gmail.cÖom"
        self.assertTrue(
            EmailMixin.check_email(email), "Email-address {} recognized as False"
        )

        email = "anK.Mä@k.itraÖi326@gm-ail.com"
        self.assertFalse(
            EmailMixin.check_email(email), "Email-address {} recognized as False"
        )

        email = "anK.Mä%k.itraÖi326@gm-ail.com"
        self.assertFalse(
            EmailMixin.check_email(email), "Email-address {} recognized as False"
        )


"""
- Doch noch mal Authentifizierung checken
- OS3 Fehler
"""
