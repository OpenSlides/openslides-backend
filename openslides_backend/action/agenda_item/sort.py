from ...models.agenda_item import AgendaItem
from ..action import register_action
from ..base import Action, ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..sort_generic import TreeSortMixin


@register_action("agenda_item.sort")
class AgendaItemSort(TreeSortMixin, Action):
    """
    Action to sort agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_sort_schema()

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        if not isinstance(payload, dict):
            raise TypeError("ActionPayload for this action must be a dictionary.")
        return self.sort_tree(
            nodes=payload["nodes"],
            meeting_id=payload["meeting_id"],
            weight_key="weight",
            parent_id_key="parent_id",
            children_ids_key="child_ids",
        )
