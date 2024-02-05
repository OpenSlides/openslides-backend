from typing import Any

from ....models.models import Meeting
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import GetMeetingIdFromIdMixin


@register_action("meeting.unset_font")
class MeetingUnsetFontAction(UpdateAction, GetMeetingIdFromIdMixin):
    """
    Action to unset a font form a meeting.
    """

    model = Meeting()
    schema = DefaultSchema(Meeting()).get_update_schema(
        additional_required_fields={
            "place": {"type": "string", "minLength": 1},
        },
    )
    permission = Permissions.Meeting.CAN_MANAGE_LOGOS_AND_FONTS

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        place = instance.pop("place")
        instance[f"font_{place}_id"] = None
        return instance
