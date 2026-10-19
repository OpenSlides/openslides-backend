from ....models.models import User
from ....shared.interfaces.event import Event, EventType
from ....shared.interfaces.write_request import WriteRequest
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .user_mixins import UserMixin


@register_action("user.block_session_id")
class UserBlockSessionID(
    UserMixin,
):
    """
    Action to block a session ID of a user
    """

    model = User()
    schema = DefaultSchema(User()).get_create_schema(optional_properties=[])

    def perform(self, action_data, user_id, **kwargs):
        try:
            encoded_logout_token = action_data[0]["logout_token"].split(
                "logout_token="
            )[1]
        except Exception as e:
            self.logger.error(
                f"Block Session ID: Malformed logout token request: {action_data} {e}"
            )
            return

        # Validate logout token and extract session id
        session_id = self.auth.decode_logout_token(encoded_logout_token)

        # Emit session id block via database signal
        if not session_id:
            self.logger.error(
                "Block Session ID: Session ID not present in logout token"
            )
            return

        # Write session id to database blocklist
        self.datastore.write(
            WriteRequest(
                events=[
                    Event(
                        type=EventType.Create,
                        collection="blocked_sessions",
                        fields={"session_id": str(session_id)},
                    )
                ]
            )
        )

        write_request = self.build_write_request()
        return (write_request, self.results)
