from ...models.models import Motion
from ..base import Action, ActionPayload, DataSet, DummyAction
from ..default_schema import DefaultSchema
from ..register import register_action
from ..sort_generic import TreeSortMixin


@register_action("motion.sort")
class MotionSort(TreeSortMixin, Action):
    """
    Action to sort motions.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_tree_sort_schema()

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        # payload is an array with exactly one item
        return self.sort_tree(
            nodes=payload[0]["tree"],
            meeting_id=payload[0]["meeting_id"],
            weight_key="sort_weight",
            parent_id_key="sort_parent_id",
            children_ids_key="sort_children_ids",
        )


@register_action("motion.sort_in_category")
class MotionSortInCategory(DummyAction):
    pass
