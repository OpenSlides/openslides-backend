from ....models.models import Poll
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PollPermissionMixin


@register_action("poll.delete")
class PollDelete(DeleteAction, PollPermissionMixin):
    """
    Action to delete polls.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_delete_schema()
