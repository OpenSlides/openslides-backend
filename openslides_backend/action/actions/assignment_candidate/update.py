from ....models.models import AssignmentCandidate
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("assignment_candidate.update", action_type=ActionType.BACKEND_INTERNAL)
class AssignmentCandidateUpdate(UpdateAction):
    """
    Action to update a assignment_candidate's weight. Should only be called by user.merge.
    """

    model = AssignmentCandidate()
    schema = DefaultSchema(AssignmentCandidate()).get_update_schema(
        required_properties=[
            "weight",
        ],
    )
