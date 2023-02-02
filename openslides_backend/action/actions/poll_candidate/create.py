from ....models.models import PollCandidate
from ...generics.create import CreateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll_candidate.create", action_type=ActionType.BACKEND_INTERNAL)
class PollCandidateCreate(CreateAction):
    """
    Internal action to create a poll candiate. It gets the meeting_id from
    its poll candidate list,
    """

    model = PollCandidate()
    schema = DefaultSchema(PollCandidate()).get_create_schema(
        required_properties=[
            "user_id",
            "poll_candidate_list_id",
            "weight",
            "meeting_id",
        ]
    )
