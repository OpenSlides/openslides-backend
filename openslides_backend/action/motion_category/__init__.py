from ..action import register_action
from ..base import DummyAction
from . import create_update_delete  # noqa


@register_action("motion_category.sort")
class MotionCategorySort(DummyAction):
    pass
