from typing import Any, Dict

from ....models.models import AssignmentCandidate
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        assignment_candidate = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            mapped_fields=["assignment_id"],
        )
        assignment = self.datastore.get(
            FullQualifiedId(
                Collection("assignment"), assignment_candidate["assignment_id"]
            ),
            mapped_fields=["phase", "meeting_id"],
        )
        if assignment.get("phase") == "finished" and not self.is_meeting_deleted(
            assignment.get("meeting_id", 0)
        ):
            raise ActionException(
                "It is not permitted to remove a candidate from a finished assignment!"
            )
        return instance
