from ...util.register import register_action
from .base_set_mediafile_action import BaseMeetingSetMediafileAction


@register_action("meeting.set_font")
class MeetingSetFontAction(BaseMeetingSetMediafileAction):
    """
    Action to set a mediafile as font.
    """

    file_type = "font"
    allowed_mimetypes = [
        "font/ttf",
        "font/woff",
        "font/woff2",
        "application/font-woff",
        "application/font-sfnt",
    ]
