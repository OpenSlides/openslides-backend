import os
import re
import smtplib
import ssl
from contextlib import contextmanager
from datetime import datetime
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from typing import Dict, Generator, List, Optional, Tuple, Union

from lxml import html as lxml_html  # type: ignore
from lxml.html.clean import clean_html  # type: ignore

from ...shared.env import is_truthy
from ...shared.exceptions import ActionException

# regular expression for validating an Email
email_checker_regex = r"[A-Z0-9._+\-ÄÖÜ]+@[A-Z0-9.\-ÄÖÜ]+\.[A-ZÄÖÜ]{2,}"

SendErrors = Dict[str, Tuple[int, bytes]]


class ConnectionSecurity:
    """constants for email connection ssl/tls"""

    NONE = "NONE"
    SSLTLS = "SSL/TLS"
    STARTTLS = "STARTTLS"

    @classmethod
    def list(cls) -> List[str]:
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

    @classmethod
    def check_settings(cls) -> None:
        if cls.connection_security not in ConnectionSecurity.list():
            raise ActionException(
                'Email-configuration: Choose one of "NONE", "STARTTLS" or "SSL/TLS" for EMAIL_CONNECTION_SECURITY environment variable'
            )


EmailSettings.check_settings()


class EmailMixin:
    @staticmethod
    def check_email(email: str) -> bool:
        """returns True with valid email, else False"""
        return bool(re.fullmatch(email_checker_regex, email, flags=(re.IGNORECASE)))

    @staticmethod
    def get_ssl_default_context() -> ssl.SSLContext:
        if EmailSettings.accept_self_signed_certificate:
            return ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        else:
            return ssl.create_default_context()

    @staticmethod
    @contextmanager
    def get_mail_connection() -> Generator[
        Union[smtplib.SMTP, smtplib.SMTP_SSL], None, None
    ]:
        connection: Optional[Union[smtplib.SMTP, smtplib.SMTP_SSL]] = None
        try:
            if EmailSettings.connection_security == ConnectionSecurity.SSLTLS:
                connection = smtplib.SMTP_SSL(
                    EmailSettings.host,
                    EmailSettings.port,
                    context=EmailMixin.get_ssl_default_context(),
                    timeout=EmailSettings.timeout,
                )
            elif EmailSettings.connection_security == ConnectionSecurity.STARTTLS:
                connection = smtplib.SMTP(  # type: ignore
                    EmailSettings.host,
                    EmailSettings.port,
                    timeout=EmailSettings.timeout,
                )
                connection.starttls(context=EmailMixin.get_ssl_default_context())
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
        client: Union[smtplib.SMTP, smtplib.SMTP_SSL],
        from_: str,
        to: Union[str, List[str]],
        subject: str,
        content: str,
        contentplain: str = "",
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
        """
        message = EmailMessage()
        if html:
            if contentplain == "":
                tree = lxml_html.fromstring(content)
                contentplain = clean_html(tree).text_content().strip()
            if contentplain:
                message.set_content(contentplain)
            message.add_alternative(content, subtype="html")
        else:
            message.set_content(content) if content else message.set_content(
                contentplain
            )

        message["From"] = from_
        message["To"] = to
        message.preamble = "You will not see this in a MIME-aware mail reader.\n"
        message.add_header("Subject", subject)
        message.add_header("Date", format_datetime(datetime.now()))
        message.add_header("Message-ID", make_msgid(domain=EmailSettings.host))
        return client.send_message(message)
