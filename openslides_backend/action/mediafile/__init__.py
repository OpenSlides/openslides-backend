from ..action import register_action
from ..base import DummyAction


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
