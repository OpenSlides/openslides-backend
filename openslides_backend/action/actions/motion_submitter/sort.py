from typing import Any, Dict

from ....models.models import MotionSubmitter
from ....permissions.permissions import Permissions
from ....shared.patterns import Collection, FullQualifiedId
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

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        yield from self.sort_linear(
            nodes=instance["motion_submitter_ids"],
            filter_id=instance["motion_id"],
            filter_str="motion_id",
        )

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        db_instance = self.datastore.fetch_model(
            FullQualifiedId(Collection("motion"), instance["motion_id"]),
            ["meeting_id"],
            exception=True,
            lock_result=True,
        )
        return db_instance["meeting_id"]
