from ..actions import register_action
from ..base import DummyAction


@register_action("motion_change_recommendation.create")
class MotionChangeRecommendationCreate(DummyAction):
    pass


@register_action("motion_change_recommendation.update")
class MotionChangeRecommendationUpdate(DummyAction):
    pass


@register_action("motion_change_recommendation.delete")
class MotionChangeRecommendationDelete(DummyAction):
    pass
