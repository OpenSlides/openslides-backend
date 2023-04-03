from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin

from ....models.models import MeetingUser
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixin import MeetingUserMixin


@register_action("meeting_user.update")
class MeetingUserUpdate(MeetingUserMixin, UpdateAction, ExtendHistoryMixin):
    """
    Action to update a meeting_user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_update_schema(
        optional_properties=[
            "about_me",
            "group_ids",
            *MeetingUserMixin.standard_fields,
        ],
    )
    permission = Permissions.User.CAN_MANAGE
    extend_history_to = "user_id"
