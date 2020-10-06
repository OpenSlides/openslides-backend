from ..base import DummyAction
from ..register import register_action
from . import create_update_delete  # noqa


@register_action("motion_block.follow_recommendations")
class MotionBlockFollowRecommendations(DummyAction):
    pass
