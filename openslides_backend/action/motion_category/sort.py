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
        # Payload is an iterable with exactly one item
        instance = next(iter(payload))
        return self.sort_tree(
            nodes=instance["tree"],
            meeting_id=instance["meeting_id"],
            weight_key="weight",
            parent_id_key="parent_id",
            children_ids_key="child_ids",
            set_level=True,
        )
