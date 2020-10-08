from ...models.models import AgendaItem
from ..base import Action, ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..register import register_action
from ..sort_generic import TreeSortMixin


@register_action("agenda_item.sort")
class AgendaItemSort(TreeSortMixin, Action):
    """
    Action to sort agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_tree_sort_schema()

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        # payload is an array with exactly one item
        return self.sort_tree(
            nodes=payload[0]["tree"],
            meeting_id=payload[0]["meeting_id"],
            weight_key="weight",
            parent_id_key="parent_id",
            children_ids_key="child_ids",
        )
