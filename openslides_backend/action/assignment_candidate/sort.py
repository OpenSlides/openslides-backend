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
        # payload is an array with exactly one item
        return self.sort_linear(
            nodes=payload[0]["candidate_ids"],
            filter_id=payload[0]["assignment_id"],
            filter_str="assignment_id",
        )
