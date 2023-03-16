from typing import Any, Dict

from ....models.models import MeetingUser
from ....permissions.permissions import Permissions
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixin import MeetingUserMixin


@register_action("meeting_user.update")
class MeetingUserUpdate(MeetingUserMixin, UpdateAction):
    """
    Action to update a meeting_user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_update_schema(
        optional_properties=[
            "about_me",
            "group_ids",
            *MeetingUserMixin.standard_fields
        ],
    )
    permission = Permissions.User.CAN_MANAGE
