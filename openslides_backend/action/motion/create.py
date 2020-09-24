from ..base import DummyAction
from ..register import register_action


@register_action("motion.create")
class MotionCreate(DummyAction):
    pass
