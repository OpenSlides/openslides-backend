from ..action import register_action
from ..base import DummyAction


@register_action("motion_workflow.create")
class MotionWorkflowCreate(DummyAction):
    pass


@register_action("motion_workflow.update")
class MotionWorkflowUpdate(DummyAction):
    pass


@register_action("motion_workflow.delete")
class MotionWorkflowDelete(DummyAction):
    pass
