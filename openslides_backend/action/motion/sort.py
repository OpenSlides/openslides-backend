from ...models.models import Motion
from ..base import Action, ActionPayload, DataSet
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
        # Payload is an iterable with exactly one item
        instance = next(iter(payload))
        return self.sort_tree(
            nodes=instance["tree"],
            meeting_id=instance["meeting_id"],
            weight_key="sort_weight",
            parent_id_key="sort_parent_id",
            children_ids_key="sort_children_ids",
        )
