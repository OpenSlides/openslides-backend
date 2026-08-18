import re
from typing import Any

from ....models.models import User
from ....shared.exceptions import ActionException
from ...util.default_schema import DefaultSchema
from ...shared.interfaces.write_request import WriteRequest
from ...shared.interfaces.event import Event, EventType
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

    def perform(self, action_data, user_id, **kwargs):
        self.logger.warning("Performing blocklist action")
        self.logger.warning(action_data)
        self.logger.warning(user_id)
        self.logger.warning(kwargs)

        request = action_data[0]["request"]

        self.logger.warning("Wow a user blocklist request came!")
        self.logger.warning(instance)
        # Validate logout token and extract session id
        session_id = self.auth.backchannel_logout(request)

        # Emit session id block via database signal
        if session_id == None or session_id == "":
            self.logger.warning("Block Session ID: No Session ID")
            return

        # TODO: Create DB Table entry
        # Write session id to blocklist
        self.datastore.write(
            WriteRequest(
                events=[
                    Event(
                        type=EventType.Create,
                        fqid=f"blocked_sessions/{os_id}",
                        fields={
                            "session_id": session_id,
                        },
                    )
                ]
            )
        )

        return instance
