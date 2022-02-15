from typing import Any, Dict

from ....models.models import MotionState
from ....permissions.permissions import Permissions
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...mixins.linear_sort_mixin import LinearSortMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("motion_state.sort")
class MotionStateSort(LinearSortMixin, SingularActionMixin, UpdateAction):
    """
    Action to sort motion states.
    """

    model = MotionState()
    schema = DefaultSchema(MotionState()).get_linear_sort_schema(
        "motion_state_ids",
        "workflow_id",
    )
    permission = Permissions.Motion.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        yield from self.sort_linear(
            nodes=instance["motion_state_ids"],
            filter_id=instance["workflow_id"],
            filter_str="workflow_id",
        )

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        workflow = self.datastore.get(
            FullQualifiedId(Collection("motion_workflow"), instance["workflow_id"]),
            ["meeting_id"],
        )
        return workflow["meeting_id"]
