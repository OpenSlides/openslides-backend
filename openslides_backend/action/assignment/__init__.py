from ..action import register_action
from ..base import DummyAction


@register_action("assignment.create")
class AssignmentCreate(DummyAction):
    pass


@register_action("assignment.update")
class AssignmentUpdate(DummyAction):
    pass


@register_action("assignment.delete")
class AssignmentDelete(DummyAction):
    pass


@register_action("assignment.sort")
class AssignmentSort(DummyAction):
    pass


@register_action("assignment.change_candidate")
class AssignmentChangeCandidate(DummyAction):
    pass


@register_action("assignment.add_self")
class AssignmentAddSelf(DummyAction):
    pass


@register_action("assignment.delete_self")
class AssignmentDeleteSelf(DummyAction):
    pass
