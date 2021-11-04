from collections import defaultdict
from smtplib import (
    SMTPAuthenticationError,
    SMTPDataError,
    SMTPRecipientsRefused,
    SMTPSenderRefused,
    SMTPServerDisconnected,
)
from ssl import SSLCertVerificationError
from time import time
from typing import Any, Dict
from urllib.parse import quote

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ...generics.update import UpdateAction
from ...mixins.send_email_mixin import EmailMixin, EmailSettings
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData

PW_FORGET_EMAIL_TEMPLATE = """You receive this email, because you have requested a new password for your OpenSlides-account.

Please open the following link and choose a new password:
/login/forget-password-confirm?user_id={user_id}&token={token}

For completeness your username: {username}"""
PW_FORGET_EMAIL_SUBJECT = "Reset your OpenSlides password"


class format_dict(defaultdict):
    def __missing__(self, key: str) -> str:
        return f"'{key}'"


@register_action("user.forget_password")
class UserForgetPassword(EmailMixin, UpdateAction):
    """
    Action to send forget password mail(s).
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        title="user forget password schema",
        additional_required_fields={"email": {"type": "string"}},
    )
    skip_archived_meeting_check = True

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            email = instance.pop("email")

            # check if email adress is valid
            if not self.check_email(EmailSettings.default_from_email):
                raise ActionException(
                    f"email '{EmailSettings.default_from_email}' is not a valid sender email address."
                )
            if not self.check_email(email):
                raise ActionException(f"'{email}' is not a valid email adress.")

            # search for users with email
            filter_ = FilterOperator("email", "=", email)
            results = self.datastore.filter(
                self.model.collection, filter_, ["id", "username"]
            )

            # try to send the mail.
            try:
                with EmailMixin.get_mail_connection() as mail_client:
                    for user in results.values():
                        if self.sendmail(
                            mail_client,
                            email,
                            PW_FORGET_EMAIL_SUBJECT,
                            self.get_email_body(
                                user["id"],
                                self.get_token(user["id"], email),
                                user["username"],
                            ),
                        ):
                            yield {"id": user["id"], "last_email_send": round(time())}
            except SMTPAuthenticationError as e:
                raise ActionException(f"SMTPAuthenticationError: {str(e)}")
            except SMTPSenderRefused as e:
                raise ActionException(f"SMTPSenderRefused: {str(e)}")
            except SSLCertVerificationError as e:
                raise ActionException(f"SSLCertVerificationError: {str(e)}")
            except Exception as e:
                raise ActionException(
                    f"Unspecified mail connection exception on sending invitation email to server {EmailSettings.host}, port {EmailSettings.port}: {str(e)}"
                )

    def get_token(self, user_id: int, email: str) -> str:
        return quote(self.auth.create_authorization_token(user_id, email))

    def get_email_body(self, user_id: int, token: str, username: str) -> str:

        body_format = format_dict(
            None,
            {
                "user_id": user_id,
                "token": token,
                "username": username,
            },
        )
        return PW_FORGET_EMAIL_TEMPLATE.format_map(body_format)

    def sendmail(
        self, mail_client: Any, email: str, email_subject: str, email_body: str
    ) -> bool:
        try:
            self.send_email(
                mail_client,
                EmailSettings.default_from_email,
                email,
                email_subject,
                email_body,
                html=False,
            )
        except SMTPRecipientsRefused as e:
            self.logger.error(f"SMTPRecipientsRefused: {str(e)}")
            return False
        except SMTPServerDisconnected as e:
            self.logger.error(f"SMTPServerDisconnected: {str(e)}")
            return False
        except SMTPDataError as e:
            self.logger.error(f"SMTPDataError: {str(e)}")
            return False
        return True

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
