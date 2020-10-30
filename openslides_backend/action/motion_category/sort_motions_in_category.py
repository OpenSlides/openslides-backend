from ...models.models import Motion
from ..base import Action, ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..register import register_action
from ..sort_generic import LinearSortMixin


@register_action("motion_category.sort_motions_in_category")
class MotionCategorySortMotionInCategorySort(LinearSortMixin, Action):
    """
    Action to motion category sort motions in categories.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_linear_sort_schema("motion_ids", "id")

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        # payload is an array with exactly one item
        return self.sort_linear(
            nodes=payload[0]["motion_ids"],
            filter_id=payload[0]["id"],
            filter_str="category_id",
            weight_key="category_weight",
        )
