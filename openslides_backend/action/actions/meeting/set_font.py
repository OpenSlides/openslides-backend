from ...util.register import register_action
from .base_set_mediafile_action import BaseMeetingSetMediafileAction


@register_action("meeting.set_font")
class MeetingSetFontAction(BaseMeetingSetMediafileAction):
    """
    Action to set a mediafile as font.
    """

    field = "font_$_id"
    allowed_mimetypes = [
        "font/ttf",
        "font/woff",
        "font/woff2",
        "application/font-woff",
        "application/font-sfnt",
    ]
    allowed_places = [
        "regular",
        "italic",
        "bold",
        "bold_italic",
        "monospace",
        "chyron_speaker_name",
        "projector_h1",
        "projector_h2",
    ]
