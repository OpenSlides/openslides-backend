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


@register_action("user.magic_link")
class SendMagicLink(
    UserMixin,
    IDPMagicLinkMixin,
    EmailMagicLinkMixin
):
    """
    Action to create a magic link for a one time session
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
        self.logger.warning("Send magic link action called")

        # Create the magic link
        magicLink = self.create_magic_link(instance["idp_id"])

        # Send it to users email
        self.send_magic_link_to(magicLinkURL, instance["email"], instance["username"])

        write_request = self.build_write_request()
        return (write_request, self.results)
