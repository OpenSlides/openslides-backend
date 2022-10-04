from ....models.models import AssignmentCandidate
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PermissionMixin


@register_action("assignment_candidate.delete")
class AssignmentCandidateDelete(PermissionMixin, DeleteAction):
    """
    Action to delete a assignment candidate.
    """

    model = AssignmentCandidate()
    schema = DefaultSchema(AssignmentCandidate()).get_delete_schema()
