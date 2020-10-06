from ..base import DummyAction
from ..register import register_action


@register_action("mediafile.create")
class MediafileCreate(DummyAction):
    pass


@register_action("mediafile.update")
class MediafileUpdate(DummyAction):
    pass


@register_action("mediafile.delete")
class MediafileDelete(DummyAction):
    pass


@register_action("mediafile.move")
class MediafileMove(DummyAction):
    pass


@register_action("mediafile.set_as_logo")
class MediafileSetAsFont(DummyAction):
    pass
