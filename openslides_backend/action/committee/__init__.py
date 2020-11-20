from ..base import DummyAction
from ..register import register_action
from . import create, delete  # noqa


@register_action("committee.update")
class CommitteeUpdate(DummyAction):
    pass
