from datetime import datetime, timezone

from typing import Any

from ....models.models import User
from ....shared.interfaces.event import Event, EventType
from ....shared.interfaces.write_request import WriteRequest
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .user_mixins import UserMixin
from ...mixins.magic_link_mixin import IDPMagicLinkMixin
from ...mixins.send_email_mixin import EmailMagicLinkMixin


@register_action("user.password_reset_link")
class SendPasswordResetLink(
    UserMixin,
    IDPMagicLinkMixin,
    EmailMagicLinkMixin
):
    """
    Action to create a link which lets a user reset their password in the IDP
    Sends the link to the users email
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        optional_properties=[
            "username",
            "idp_id",
            "email",
        ],
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        self.logger.warning("Send password reset link action called")

        # Create password reset link
        resetLinkURL = self.generate_password_reset_link(idp_id)

        # Send password reset link
        self.send_password_reset_to(resetLinkURL, instance["email"], instance["username"])

        write_request = self.build_write_request()
        return (write_request, self.results)
