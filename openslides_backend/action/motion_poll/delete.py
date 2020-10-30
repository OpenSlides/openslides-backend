from ..base import DummyAction
from ..register import register_action


@register_action("motion_poll.delete")
class MotionPollDelete(DummyAction):
    pass
