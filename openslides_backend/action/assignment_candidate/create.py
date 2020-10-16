from ...models.models import AssignmentCandidate
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action


@register_action("assignment_candidate.create")
class AssignmentCandidateCreate(CreateAction):
    """
    Action to create an assignment candidate.
    """

    model = AssignmentCandidate()
    schema = DefaultSchema(AssignmentCandidate()).get_create_schema(
        required_properties=["assignment_id", "user_id"], optional_properties=[],
    )
