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
            "comment",
            "number",
            "structure_level",
            "about_me",
            "vote_weight",
        ],
    )
    permission = Permissions.User.CAN_MANAGE
