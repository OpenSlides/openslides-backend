from collections import defaultdict
from time import time
from typing import Any, Dict
from urllib.parse import quote

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....i18n.translator import translate as _
from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ...generics.update import UpdateAction
from ...mixins.send_email_mixin import EmailSettings, EmailUtils
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


class format_dict(defaultdict):
    def __missing__(self, key: str) -> str:
        return f"'{key}'"


@register_action("user.forget_password")
class UserForgetPassword(UpdateAction):
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
        self.PW_FORGET_EMAIL_TEMPLATE = _(
            """You are receiving this email because you have requested a new password for your OpenSlides account.

Please open the following link and choose a new password:
{url}/login/forget-password-confirm?user_id={user_id}&token={token}

The link will be valid for 10 minutes."""
        )
        self.PW_FORGET_EMAIL_SUBJECT = _("Reset your OpenSlides password")
        for instance in action_data:
            email = instance.pop("email")

            # check if email adress is valid
            if not EmailUtils.check_email(EmailSettings.default_from_email):
                raise ActionException(
                    "The server was configured improperly. Please contact your administrator."
                )
            if not EmailUtils.check_email(email):
                raise ActionException(f"'{email}' is not a valid email adress.")

            # search for users with email
            filter_ = FilterOperator("email", "=", email)
            results = self.datastore.filter(
                self.model.collection, filter_, ["id", "username", "saml_id"]
            )

            organization = self.datastore.get(
                ONE_ORGANIZATION_FQID, ["url"], lock_result=False
            )
            url = organization.get("url", "")

            # try to send the mails.
            try:
                with EmailUtils.get_mail_connection() as mail_client:
                    for user in results.values():
                        if user.get("saml_id"):
                            raise ActionException(
                                f"user {user['saml_id']} is a Single Sign On user and has no local OpenSlides password."
                            )
                        username = user["username"]
                        ok, errors = EmailUtils.send_email_safe(
                            mail_client,
                            self.logger,
                            EmailSettings.default_from_email,
                            email,
                            self.PW_FORGET_EMAIL_SUBJECT + f": {username}",
                            self.get_email_body(
                                user["id"],
                                self.get_token(user["id"], email),
                                user["username"],
                                url,
                            ),
                            html=False,
                        )
                        if ok:
                            yield {"id": user["id"], "last_email_sent": round(time())}
            except ActionException as e:
                self.logger.error(f"send mail action exception: {str(e)}")
                raise
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
        return self.PW_FORGET_EMAIL_TEMPLATE.format_map(body_format)

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
