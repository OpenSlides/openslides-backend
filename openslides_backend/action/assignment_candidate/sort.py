from ...models.models import AssignmentCandidate
from ..base import Action, ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..register import register_action
from ..sort_generic import LinearSortMixin


@register_action("assignment_candidate.sort")
class AssignmentCandidateSort(LinearSortMixin, Action):
    """
    Action to sort assignment candidates.
    """

    model = AssignmentCandidate()
    schema = DefaultSchema(AssignmentCandidate()).get_linear_sort_schema(
        "candidate_ids", "assignment_id",
    )

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        # Payload is an iterable with exactly one item
        instance = next(iter(payload))
        return self.sort_linear(
            nodes=instance["candidate_ids"],
            filter_id=instance["assignment_id"],
            filter_str="assignment_id",
        )
