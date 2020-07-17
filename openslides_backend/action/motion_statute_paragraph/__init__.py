from ..action import register_action
from ..base import DummyAction


@register_action("motion_statute_paragraph.create")
class MotionStatuteParagraphCreate(DummyAction):
    pass


@register_action("motion_statute_paragraph.update")
class MotionStatuteParagraphUpdate(DummyAction):
    pass


@register_action("motion_statute_paragraph.delete")
class MotionStatuteParagraphDelete(DummyAction):
    pass
