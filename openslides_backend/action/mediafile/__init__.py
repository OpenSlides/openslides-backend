from ..base import DummyAction
from ..register import register_action
from . import create_directory, delete, update, upload  # noqa


@register_action("mediafile.move")
class MediafileMove(DummyAction):
    pass
