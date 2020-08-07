from ..action import register_action
from ..base import DummyAction


@register_action("motion.create")
class MotionCreate(DummyAction):
    pass
