from ..base import DummyAction
from ..register import register_action
from . import delete, set_as_font, set_as_logo  # noqa


@register_action("mediafile.create")
class MediafileCreate(DummyAction):
    pass


@register_action("mediafile.update")
class MediafileUpdate(DummyAction):
    pass


@register_action("mediafile.move")
class MediafileMove(DummyAction):
    pass
