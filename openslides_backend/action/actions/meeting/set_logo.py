from ...util.register import register_action
from .base_set_mediafile_action import BaseMeetingSetMediafileAction


@register_action("meeting.set_logo")
class MeetingSetLogoAction(BaseMeetingSetMediafileAction):
    """
    Action to set a mediafile as logo.
    """

    file_type = "logo"
    allowed_mimetypes = ["image/png", "image/jpeg", "image/gif", "image/svg+xml"]
