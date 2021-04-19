from typing import Any, Dict

from ....models.models import AssignmentCandidate
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PermissionMixin


@register_action("assignment_candidate.create")
class AssignmentCandidateCreate(PermissionMixin, CreateActionWithInferredMeeting):
    """
    Action to create an assignment candidate.
    """

    model = AssignmentCandidate()
    schema = DefaultSchema(AssignmentCandidate()).get_create_schema(
        required_properties=["assignment_id", "user_id"],
        optional_properties=[],
    )

    relation_field_for_meeting = "assignment_id"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        assignment = self.datastore.get(
            FullQualifiedId(Collection("assignment"), instance["assignment_id"]),
            mapped_fields=["phase"],
        )
        if assignment.get("phase") == "finished":
            raise ActionException(
                "It is not permitted to add a candidate to a finished assignment!"
            )
        return instance
