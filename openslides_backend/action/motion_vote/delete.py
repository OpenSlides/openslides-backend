from ..base import DummyAction
from ..register import register_action


@register_action("motion_vote.delete")
class MotionVoteDelete(DummyAction):
    pass
