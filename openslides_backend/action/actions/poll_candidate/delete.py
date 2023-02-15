from ....models.models import PollCandidate
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll_candidate.delete", action_type=ActionType.BACKEND_INTERNAL)
class PollCandidateDelete(DeleteAction):
    """
    Internal action to delete a poll candidate.
    """

    model = PollCandidate()
    schema = DefaultSchema(PollCandidate()).get_delete_schema()
