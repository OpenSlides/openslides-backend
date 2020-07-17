from ..action import register_action
from ..base import DummyAction


@register_action("tag.create")
class TagCreate(DummyAction):
    pass


@register_action("tag.update")
class TagUpdate(DummyAction):
    pass


@register_action("tag.delete")
class TagDelete(DummyAction):
    pass
