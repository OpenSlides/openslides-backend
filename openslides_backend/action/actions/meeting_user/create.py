from typing import Any, Dict

from ....models.models import MeetingUser
from ....permissions.permissions import Permissions
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixin import MeetingUserMixin


@register_action("meeting_user.create")
class MeetingUserCreate(MeetingUserMixin, CreateAction):
    """
    Action to create a meeting user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_create_schema(
        required_properties=["user_id", "meeting_id"],
        optional_properties=[
            "about_me",
            "group_ids",
            *MeetingUserMixin.standard_fields
        ],
    )
    permission = Permissions.User.CAN_MANAGE
