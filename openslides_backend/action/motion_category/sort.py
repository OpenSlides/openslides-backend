from ...models.models import MotionCategory
from ..base import Action, ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..register import register_action
from ..sort_generic import TreeSortMixin


@register_action("motion_category.sort")
class MotionCategorySort(TreeSortMixin, Action):
    """
    Action to sort motion categories.
    """

    model = MotionCategory()
    schema = DefaultSchema(MotionCategory()).get_tree_sort_schema()

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        return self.sort_tree(
            nodes=payload[0]["tree"],
            meeting_id=payload[0]["meeting_id"],
            weight_key="weight",
            parent_id_key="parent_id",
            children_ids_key="child_ids",
        )
