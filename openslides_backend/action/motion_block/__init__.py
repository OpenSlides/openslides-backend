from ..action import register_action
from ..base import DummyAction


@register_action("motion_block.create")
class MotionBlockCreate(DummyAction):
    pass


@register_action("motion_block.update")
class MotionBlockUpdate(DummyAction):
    pass


@register_action("motion_block.delete")
class MotionBlockDelete(DummyAction):
    pass


@register_action("motion_block.follow_recommendations")
class MotionBlockFollowRecommendations(DummyAction):
    pass
