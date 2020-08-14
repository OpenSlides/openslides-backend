from ..action import register_action
from ..base import DummyAction
from . import create_update_delete  # noqa


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
