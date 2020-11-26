from ...action import DummyAction
from ...util.register import register_action


@register_action("motion_poll.delete")
class MotionPollDelete(DummyAction):
    pass
