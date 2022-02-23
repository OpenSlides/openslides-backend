from ....models.models import Motion, MotionSubmitter
from ....permissions.permissions import Permissions
from ....shared.filters import FilterOperator
from ...generics.update import UpdateAction
from ...mixins.linear_sort_mixin import LinearSortMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("motion_submitter.sort")
class MotionSubmitterSort(LinearSortMixin, SingularActionMixin, UpdateAction):
    """
    Action to sort motion comment sections.
    """

    model = MotionSubmitter()
    schema = DefaultSchema(MotionSubmitter()).get_linear_sort_schema(
        "motion_submitter_ids", "motion_id"
    )
    permission = Permissions.Motion.CAN_MANAGE_METADATA
    permission_model = Motion()
    permission_id = "motion_id"

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        yield from self.sort_linear(
            instance["motion_submitter_ids"],
            FilterOperator("motion_id", "=", instance["motion_id"]),
        )
