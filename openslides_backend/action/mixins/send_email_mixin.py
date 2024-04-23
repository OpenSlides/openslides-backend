import os
import re
import smtplib
import ssl
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from typing import Any

from openslides_backend.shared.interfaces.logging import Logger

from ...shared.env import is_truthy
from ...shared.exceptions import ActionException
from ...shared.html import get_text_from_html
from ..action import Action

SendErrors = dict[str, tuple[int, bytes]]


class ConnectionSecurity:
    """constants for email connection ssl/tls"""

    NONE = "NONE"
    SSLTLS = "SSL/TLS"
    STARTTLS = "STARTTLS"

    @classmethod
    def list(cls) -> list[str]:
        return [
            value
            for attr in dir(cls)
            if not callable(value := getattr(cls, attr)) and not attr.startswith("_")
        ]


class EmailSettings:
    host: str = os.environ.get("EMAIL_HOST", "localhost")
    port: int = int(os.environ.get("EMAIL_PORT", "465"))
    user: str = os.environ.get("EMAIL_HOST_USER", "")
    password: str = os.environ.get("EMAIL_HOST_PASSWORD", "")
    connection_security: str = os.environ.get("EMAIL_CONNECTION_SECURITY", "SSL/TLS")
    timeout: int = int(os.environ.get("EMAIL_TIMEOUT", "5"))
    accept_self_signed_certificate: bool = is_truthy(
        os.environ.get("EMAIL_ACCEPT_SELF_SIGNED_CERTIFICATE", "false")
    )
    default_from_email = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com")

    @classmethod
    def check_settings(cls) -> None:
        if cls.connection_security not in ConnectionSecurity.list():
            raise ActionException(
                'Email-configuration: Choose one of "NONE", "STARTTLS" or "SSL/TLS" for EMAIL_CONNECTION_SECURITY environment variable'
            )


EmailSettings.check_settings()


class EmailUtils:
    SENDER_NAME_FORBIDDEN_CHARS = ("[", "]", "\\")

    @staticmethod
    def check_email(email: str) -> bool:
        """returns True with valid email, else False"""
        email_regex = r"[A-Z0-9._+\-ÄÖÜ]+@[A-Z0-9.\-ÄÖÜ]+\.[A-ZÄÖÜ]{2,}"
        return bool(re.fullmatch(email_regex, email, flags=(re.IGNORECASE)))

    @staticmethod
    def get_ssl_default_context() -> ssl.SSLContext:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        if EmailSettings.accept_self_signed_certificate:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.VerifyMode.CERT_NONE
        return ctx

    @staticmethod
    @contextmanager
    def get_mail_connection() -> Generator[smtplib.SMTP | smtplib.SMTP_SSL, None, None]:
        connection: smtplib.SMTP | smtplib.SMTP_SSL | None = None
        try:
            if EmailSettings.connection_security == ConnectionSecurity.SSLTLS:
                connection = smtplib.SMTP_SSL(
                    EmailSettings.host,
                    EmailSettings.port,
                    context=EmailUtils.get_ssl_default_context(),
                    timeout=EmailSettings.timeout,
                )
            elif EmailSettings.connection_security == ConnectionSecurity.STARTTLS:
                connection = smtplib.SMTP(  # type: ignore
                    EmailSettings.host,
                    EmailSettings.port,
                    timeout=EmailSettings.timeout,
                )
                connection.starttls(context=EmailUtils.get_ssl_default_context())
            else:
                connection = smtplib.SMTP(  # type: ignore
                    EmailSettings.host,
                    EmailSettings.port,
                    timeout=EmailSettings.timeout,
                )
            if EmailSettings.user and EmailSettings.password:
                connection.login(EmailSettings.user, EmailSettings.password)
            yield connection
        finally:
            if connection:
                connection.close()

    @staticmethod
    def send_email(
        client: smtplib.SMTP | smtplib.SMTP_SSL,
        from_: str,
        to: str | list[str],
        subject: str,
        content: str,
        contentplain: str = "",
        reply_to: str = "",
        html: bool = True,
    ) -> SendErrors:
        """
        Construct and send the email on the given connect
        Default is a html-email with 'html' set to True.
        Then 'content' is expected to be the html-body of the mail
        and 'contentplain' the alternative plaintext.
        If 'contentplain' is an empty string, the method will build a
        plaintext-content from 'content'. If 'contentplain' is
        a None, the client will send a html-only mail.

        With 'html' set to False, 'content' will be used as plaintext.

        Return value: The method only returns, if the mail was sent to
            minimum 1 recipient. Otherwise the method throws an exception.
            The return value is a dict of errors, where the key is a
            recipients email address and the value a tuple of SMTP-error-code
            and error message.
            You only have to check the methods return code, if there
            could be more than one recipient in the to-address of an email,
            see smtplib's method sendmail.
        """
        message = EmailMessage()
        if html:
            if contentplain == "":
                contentplain = get_text_from_html(content)
            if contentplain:
                message.set_content(contentplain)
            message.add_alternative(content, subtype="html")
        else:
            (
                message.set_content(content)
                if content
                else message.set_content(contentplain)
            )

        message["From"] = from_
        message["To"] = to if isinstance(to, str) else ", ".join(to)
        message.preamble = "You will not see this in a MIME-aware mail reader.\n"
        message.add_header("Subject", subject)
        message.add_header("Date", format_datetime(datetime.now()))
        message.add_header("Message-ID", make_msgid(domain=EmailSettings.host))
        if reply_to:
            message.add_header("Reply-To", reply_to)
        return client.send_message(message)

    @staticmethod
    def send_email_safe(
        client: smtplib.SMTP | smtplib.SMTP_SSL,
        logger: Logger,
        from_: str,
        to: str | list[str],
        subject: str,
        content: str,
        contentplain: str = "",
        reply_to: str = "",
        html: bool = True,
    ) -> tuple[bool, SendErrors]:
        try:
            return True, EmailUtils.send_email(
                client, from_, to, subject, content, contentplain, reply_to, html
            )
        except smtplib.SMTPException as e:
            logger.error(f"{type(e).__name__}: {str(e)}")
        return False, {}


class EmailCheckMixin(Action):
    check_email_field: str

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        if instance.get(self.check_email_field):
            instance[self.check_email_field] = instance[self.check_email_field].strip()
            if not EmailUtils.check_email(instance[self.check_email_field]):
                raise ActionException(f"{self.check_email_field} must be valid email.")
        return super().update_instance(instance)


class EmailSenderCheckMixin(Action):
    check_email_sender_field = "users_email_sender"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        if instance.get(self.check_email_sender_field):
            if any(
                entry in instance[self.check_email_sender_field]
                for entry in EmailUtils.SENDER_NAME_FORBIDDEN_CHARS
            ):
                raise ActionException(
                    f"""{self.check_email_sender_field} must not contain '{"', '".join(EmailUtils.SENDER_NAME_FORBIDDEN_CHARS)}'."""
                )
        instance = super().update_instance(instance)
        return instance
