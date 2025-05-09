from typing import Any

from ....models.models import AssignmentCandidate
from ....services.database.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import PermissionMixin


@register_action("assignment_candidate.create")
class AssignmentCandidateCreate(PermissionMixin, CreateActionWithInferredMeeting):
    """
    Action to create an assignment candidate.
    """

    model = AssignmentCandidate()
    schema = DefaultSchema(AssignmentCandidate()).get_create_schema(
        required_properties=["assignment_id", "meeting_user_id"],
        optional_properties=[],
    )
    history_information = "Candidate added"
    history_relation_field = "assignment_id"

    relation_field_for_meeting = "assignment_id"

    def prefetch(self, action_data: ActionData) -> None:
        self.datastore.get_many(
            [
                GetManyRequest(
                    "assignment",
                    list(
                        {
                            instance["assignment_id"]
                            for instance in action_data
                            if instance.get("assignment_id")
                        }
                    ),
                    ["meeting_id", "phase", "candidate_ids"],
                )
            ]
        )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        assignment = self.datastore.get(
            fqid_from_collection_and_id("assignment", instance["assignment_id"]),
            mapped_fields=["phase"],
        )
        if assignment.get("phase") == "finished":
            raise ActionException(
                "It is not permitted to add a candidate to a finished assignment!"
            )
        return instance
