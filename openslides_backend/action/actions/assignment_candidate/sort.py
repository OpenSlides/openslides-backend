from ....models.models import AssignmentCandidate
from ...generics.update import UpdateAction
from ...mixins.linear_sort_mixin import LinearSortMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("assignment_candidate.sort")
class AssignmentCandidateSort(LinearSortMixin, SingularActionMixin, UpdateAction):
    """
    Action to sort assignment candidates.
    """

    model = AssignmentCandidate()
    schema = DefaultSchema(AssignmentCandidate()).get_linear_sort_schema(
        "candidate_ids",
        "assignment_id",
    )

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        yield from self.sort_linear(
            nodes=instance["candidate_ids"],
            filter_id=instance["assignment_id"],
            filter_str="assignment_id",
        )
