from ..base import DummyAction
from ..register import register_action
from . import create_directory, delete, set_as_font, update, upload  # noqa


@register_action("mediafile.move")
class MediafileMove(DummyAction):
    pass
