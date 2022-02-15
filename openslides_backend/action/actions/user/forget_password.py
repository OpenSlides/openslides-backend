from collections import defaultdict
from time import time
from typing import Any, Dict
from urllib.parse import quote

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...mixins.send_email_mixin import EmailMixin, EmailSettings
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData

PW_FORGET_EMAIL_TEMPLATE = """You are receiving this email because you have requested a new password for your OpenSlides-account.

Please open the following link and choose a new password:
{url}/login/forget-password-confirm?user_id={user_id}&token={token}

For completeness your username: {username}"""
PW_FORGET_EMAIL_SUBJECT = "Reset your OpenSlides password"
ONE_ORGANIZATION = 1


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
                    "The server was configured improperly. Please contact your administrator."
                )
            if not self.check_email(email):
                raise ActionException(f"'{email}' is not a valid email adress.")

            # search for users with email
            filter_ = FilterOperator("email", "=", email)
            results = self.datastore.filter(
                self.model.collection, filter_, ["id", "username"]
            )

            organization = self.datastore.get(
                FullQualifiedId(Collection("organization"), ONE_ORGANIZATION), ["url"]
            )
            url = organization.get("url", "")

            # try to send the mails.
            try:
                with EmailMixin.get_mail_connection() as mail_client:
                    for user in results.values():
                        ok, _ = self.send_email_safe(
                            mail_client,
                            self.logger,
                            EmailSettings.default_from_email,
                            email,
                            PW_FORGET_EMAIL_SUBJECT,
                            self.get_email_body(
                                user["id"],
                                self.get_token(user["id"], email),
                                user["username"],
                                url,
                            ),
                            html=False,
                        )
                        if ok:
                            yield {"id": user["id"], "last_email_send": round(time())}
            except Exception as e:
                self.logger.error(f"General send mail exception: {str(e)}")
                raise ActionException(
                    "The server was configured improperly. Please contact your administrator."
                )

    def get_token(self, user_id: int, email: str) -> str:
        return quote(self.auth.create_authorization_token(user_id, email))

    def get_email_body(self, user_id: int, token: str, username: str, url: str) -> str:
        body_format = format_dict(
            None,
            {
                "user_id": user_id,
                "token": token,
                "username": username,
                "url": url,
            },
        )
        return PW_FORGET_EMAIL_TEMPLATE.format_map(body_format)

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
