from ..action import register_action
from ..base import DummyAction


@register_action("motion_category.create")
class MotionCategoryCreate(DummyAction):
    pass


@register_action("motion_category.update")
class MotionCategoryUpdate(DummyAction):
    pass


@register_action("motion_category.delete")
class MotionCategoryDelete(DummyAction):
    pass


@register_action("motion_category.sort")
class MotionCategorySort(DummyAction):
    pass
