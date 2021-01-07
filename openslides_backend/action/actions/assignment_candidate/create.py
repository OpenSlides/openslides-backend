from ....models.models import AssignmentCandidate
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("assignment_candidate.create")
class AssignmentCandidateCreate(CreateActionWithInferredMeeting):
    """
    Action to create an assignment candidate.
    """

    model = AssignmentCandidate()
    schema = DefaultSchema(AssignmentCandidate()).get_create_schema(
        required_properties=["assignment_id", "user_id"],
        optional_properties=[],
    )

    relation_field_for_meeting = "assignment_id"
