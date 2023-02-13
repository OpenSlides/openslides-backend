from ....models.models import PollCandidateList
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll_candidate_list.delete", action_type=ActionType.BACKEND_INTERNAL)
class PollCandidateListDelete(DeleteAction):
    """
    Internal action to delete a poll candidate.
    """

    model = PollCandidateList()
    schema = DefaultSchema(PollCandidateList()).get_delete_schema()
