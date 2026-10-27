from datetime import datetime, timezone

from typing import Any

from ....models.models import User
from ....shared.interfaces.event import Event, EventType
from ....shared.interfaces.write_request import WriteRequest
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .user_mixins import UserMixin
from ...mixins.magic_link_mixin import IDPMagicLinkMixin
from ...mixins.send_email_mixin import EmailUtils


@register_action("user.magic_link")
class SendMagicLink(
    UserMixin,
    IDPMagicLinkMixin
):
    """
    Action to create a magic link for a one time session
    Sends the link to the users email
    """

    model = User()
    schema = DefaultSchema(User()).get_create_schema(optional_properties=[])

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        self.logger.warning("Send magic link action called")

        # Create the magic link
        magicLink = self.create_magic_link(instance["idp_id"])

        # Send it to users email
        with EmailUtils.get_mail_connection() as mail_client:
            username = user["username"]
            ok, errors = EmailUtils.send_email_safe(
                mail_client,
                self.logger,
                EmailSettings.default_from_email,
                user["email"],
                self.PW_FORGET_EMAIL_SUBJECT + f": {username}",
                self.get_email_body(
                    user["id"],
                    self.get_token(user["id"], user["email"]),
                    user["username"],
                    url,
                ),
                html=False,
            )
            if ok:
                yield {
                    "id": user["id"],
                    "last_email_sent": datetime.now(ZoneInfo("UTC")),
                }

        write_request = self.build_write_request()
        return (write_request, self.results)
