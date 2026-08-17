import re
from typing import Any

from ....models.models import User
from ....shared.exceptions import ActionException
from ...util.default_schema import DefaultSchema
from .password_mixins import SetPasswordMixin
from .user_mixins import UserMixin


@register_action("user.block_session_id")
class UserBlockSessionID(
    UserMixin,
):
    """
    Action to block a session ID of a user
    """

    model = User()
    schema = DefaultSchema(User()).get_create_schema(
        optional_properties=[]
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        request = None

        # Validate logout token and extract session id
        session_id = self.auth.backchannel_logout(request)

        # Emit session id block via database signal
        if session_id == None or session_id == "":
            self.logger.warning("Block Session ID: No Session ID")
            return

        # TODO: Create DB Table entry

        return instance
