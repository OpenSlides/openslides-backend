from ...models.models import MotionCategory
from ..action import register_action
from ..base import Action, ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..sort_generic import TreeSortMixin


@register_action("motion_category.sort")
class MotionCategorySort(TreeSortMixin, Action):
    """
    Action to sort motion categories.
    """

    model = MotionCategory()
    schema = DefaultSchema(MotionCategory()).get_tree_sort_schema()

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        if not isinstance(payload, dict):
            raise TypeError("ActionPayload for this action must be a dictionary.")
        return self.sort_tree(
            nodes=payload["tree"],
            meeting_id=payload["meeting_id"],
            weight_key="weight",
            parent_id_key="parent_id",
            children_ids_key="child_ids",
        )
