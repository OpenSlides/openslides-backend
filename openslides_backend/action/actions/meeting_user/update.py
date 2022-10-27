from ....models.models import MeetingUser
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_user.update")
class MeetingUserUpdate(UpdateAction):
    """
    Action to update a meeting_user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_update_schema(
        optional_properties=[
            "meeting_id",
            "user_id",
            # TODO: add moved fields here.
        ],
    )
    permission = Permissions.User.CAN_MANAGE
