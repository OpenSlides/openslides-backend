from ...action import DummyAction
from ...util.register import register_action


@register_action("motion_vote.delete")
class MotionVoteDelete(DummyAction):
    pass
