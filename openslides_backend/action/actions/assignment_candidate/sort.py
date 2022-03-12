from ....models.models import Assignment, AssignmentCandidate
from ....permissions.permissions import Permissions
from ....shared.filters import And, FilterOperator
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
    permission_model = Assignment()
    permission_id = "assignment_id"
    permission = Permissions.Assignment.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        meeting_id = self.get_meeting_id(instance)
        yield from self.sort_linear(
            instance["candidate_ids"],
            And(
                FilterOperator("assignment_id", "=", instance["assignment_id"]),
                FilterOperator("meeting_id", "=", meeting_id),
            ),
        )
