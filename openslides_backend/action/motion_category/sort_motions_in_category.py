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
        # Payload is an iterable with exactly one item
        instance = next(iter(payload))
        return self.sort_linear(
            nodes=instance["motion_ids"],
            filter_id=instance["id"],
            filter_str="category_id",
            weight_key="category_weight",
        )
