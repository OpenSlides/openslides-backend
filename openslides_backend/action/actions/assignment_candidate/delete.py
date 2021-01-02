from ....models.models import AssignmentCandidate
from ...action import PERMISSION_SPECIAL_CASE
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("assignment_candidate.delete")
class AssignmentCandidateDelete(DeleteAction):
    """
    Action to delete a assignment candidate.
    """

    model = AssignmentCandidate()
    schema = DefaultSchema(AssignmentCandidate()).get_delete_schema()
    permission_description = PERMISSION_SPECIAL_CASE
