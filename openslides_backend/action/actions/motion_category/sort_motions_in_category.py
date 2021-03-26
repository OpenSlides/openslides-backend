from typing import Any, Dict

from ....models.models import Motion
from ....permissions.permissions import Permissions
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...mixins.linear_sort_mixin import LinearSortMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("motion_category.sort_motions_in_category")
class MotionCategorySortMotionInCategorySort(
    LinearSortMixin, SingularActionMixin, UpdateAction
):
    """
    Action to motion category sort motions in categories.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_linear_sort_schema("motion_ids", "id")
    permission = Permissions.Motion.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        yield from self.sort_linear(
            nodes=instance["motion_ids"],
            filter_id=instance["id"],
            filter_str="category_id",
            weight_key="category_weight",
        )

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        motion_category = self.datastore.get(
            FullQualifiedId(Collection("motion_category"), instance["id"]),
            ["meeting_id"],
        )
        return motion_category["meeting_id"]
