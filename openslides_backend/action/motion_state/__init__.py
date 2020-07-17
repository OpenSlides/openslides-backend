from ..action import register_action
from ..base import DummyAction


@register_action("motion_state.create")
class MotionStateCreate(DummyAction):
    pass


@register_action("motion_state.update")
class MotionStateUpdate(DummyAction):
    pass


@register_action("motion_state.delete")
class MotionStateDelete(DummyAction):
    pass
