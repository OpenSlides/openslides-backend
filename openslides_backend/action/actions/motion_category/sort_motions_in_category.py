from ....models.models import Motion, MotionCategory
from ....permissions.permissions import Permissions
from ....shared.filters import And, FilterOperator
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
    permission_model = MotionCategory()

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        meeting_id = self.get_meeting_id(instance)
        yield from self.sort_linear(
            instance["motion_ids"],
            And(
                FilterOperator("category_id", "=", instance["id"]),
                FilterOperator("meeting_id", "=", meeting_id),
            ),
            weight_key="category_weight",
        )
