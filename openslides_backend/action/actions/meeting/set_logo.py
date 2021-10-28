from typing import Any, Dict

from ...util.register import register_action
from .base_set_mediafile_action import BaseMeetingSetMediafileAction


@register_action("meeting.set_logo")
class MeetingSetLogoAction(BaseMeetingSetMediafileAction):
    """
    Action to set a mediafile as logo.
    """

    field = "logo_$_id"
    allowed_mimetypes = ["image/png", "image/jpeg", "image/gif"]

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        return instance["id"]
