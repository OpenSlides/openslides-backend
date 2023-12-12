import smtplib
import ssl
from email.headerregistry import Address

import pytest

from openslides_backend.action.mixins.send_email_mixin import EmailSettings, EmailUtils
from tests.system.action.base import BaseActionTestCase
from tests.system.action.mail_base import AIOHandler, AiosmtpdServerManager


class SendMailWithSmtpServer(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sender = "sender@example.com"
        self.password = "secret"
        self.receivers = ["receiver1@example.com", "receiver2@example.com"]
        EmailSettings.host = "127.0.0.1"
        EmailSettings.port = 25
        EmailSettings.timeout = 5
        EmailSettings.user = ""  # important to reset these settings
        EmailSettings.password = ""

    # send tests with different connection_securities without authorization
    def test_send_ssl_tls(self) -> None:
        EmailSettings.connection_security = "SSL/TLS"
        EmailSettings.accept_self_signed_certificate = True
        EmailSettings.port = 993

        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            with EmailUtils.get_mail_connection() as mail_client:
                EmailUtils.send_email(
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
        EmailSettings.port = 143

        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            with EmailUtils.get_mail_connection() as mail_client:
                response = EmailUtils.send_email(
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
        with AiosmtpdServerManager(handler):
            with EmailUtils.get_mail_connection() as mail_client:
                response = EmailUtils.send_email(
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
        EmailSettings.port = 993
        EmailSettings.user = self.sender
        EmailSettings.password = self.password

        handler = AIOHandler()
        with AiosmtpdServerManager(handler, auth=True):
            with EmailUtils.get_mail_connection() as mail_client:
                EmailUtils.send_email(
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
        EmailSettings.port = 143
        EmailSettings.user = self.sender
        EmailSettings.password = self.password

        handler = AIOHandler()
        with AiosmtpdServerManager(handler, auth=True):
            with EmailUtils.get_mail_connection() as mail_client:
                response = EmailUtils.send_email(
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
        with AiosmtpdServerManager(handler, auth=True):
            with EmailUtils.get_mail_connection() as mail_client:
                response = EmailUtils.send_email(
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
        with AiosmtpdServerManager(handler, auth=True):
            with pytest.raises(smtplib.SMTPAuthenticationError) as e:
                with EmailUtils.get_mail_connection():
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
        with AiosmtpdServerManager(handler, auth=True):
            with EmailUtils.get_mail_connection() as mail_client:
                with pytest.raises(smtplib.SMTPSenderRefused) as e:
                    EmailUtils.send_email(
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
        with AiosmtpdServerManager(handler):
            with EmailUtils.get_mail_connection() as mail_client:
                response = EmailUtils.send_email(
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
        with AiosmtpdServerManager(handler):
            with EmailUtils.get_mail_connection() as mail_client:
                response = EmailUtils.send_email(
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

    # General connection Problems client -> server
    def test_connection_wrong_port(self) -> None:
        """Server started on 25, client tries on 26"""
        EmailSettings.connection_security = "NONE"
        EmailSettings.port = 25

        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            EmailSettings.port = 26
            with pytest.raises(ConnectionRefusedError):
                EmailUtils.get_mail_connection().__enter__()

    def test_connection_interrupted(self) -> None:
        EmailSettings.connection_security = "NONE"
        handler = AIOHandler()
        with AiosmtpdServerManager(handler) as server:
            with EmailUtils.get_mail_connection() as mail_client:
                with pytest.raises(smtplib.SMTPServerDisconnected):
                    server.stop()
                    EmailUtils.send_email(
                        mail_client,
                        self.sender,
                        self.receivers,
                        subject="Test-email",
                        content="Hi\r\nThis is some plain text content!",
                        html=False,
                    )

    def test_self_signed_not_accepted(self) -> None:
        EmailSettings.connection_security = "STARTTLS"
        EmailSettings.port = 143
        EmailSettings.accept_self_signed_certificate = False

        with AiosmtpdServerManager(AIOHandler()):
            with pytest.raises(
                ssl.SSLCertVerificationError,
                match="certificate verify failed: self-signed certificate",
            ):
                EmailUtils.get_mail_connection().__enter__()

    # test invalid receivers
    def test_invalid_receiver_all(self) -> None:
        """Exception is only thrown, if ALL recipients are invalid"""
        EmailSettings.connection_security = "NONE"
        EmailSettings.port = 25

        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            with EmailUtils.get_mail_connection() as mail_client:
                with pytest.raises(smtplib.SMTPRecipientsRefused) as e:
                    EmailUtils.send_email(
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
        with AiosmtpdServerManager(handler):
            with EmailUtils.get_mail_connection() as mail_client:
                receivers = self.receivers + ["invalidQexample1.com"]
                response = EmailUtils.send_email(
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

    # Test sender with name
    def test_sender_with_name(self) -> None:
        EmailSettings.connection_security = "NONE"
        EmailSettings.port = 25

        sender = Address("Name of sender", addr_spec=self.sender)
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            with EmailUtils.get_mail_connection() as mail_client:
                response = EmailUtils.send_email(
                    mail_client,
                    sender,
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
            f"From: Name of sender <{self.sender}>",
            handler.emails[0]["data"],
        )
        self.assertNotIn(
            'Content-Type: text/html; charset="utf-8"',
            handler.emails[0]["data"],
        )


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
                EmailUtils.check_email(email),
                f"Email-address {email} recognized as False",
            )

    def test_check_invalid_emails(self) -> None:
        emails = (
            "anK.Mä@k.itraÖi326@gm-ail.com",
            "anK.Mä%k.itraÖi326@gm-ail.com",
            "k[6@gm-ail.com",
            "k]6@gm-ail.com",
            "k\6@gm-ail.com",
        )

        for email in emails:
            self.assertFalse(
                EmailUtils.check_email(email),
                f"Email-address {email} recognized as True",
            )
