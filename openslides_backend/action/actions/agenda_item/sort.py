from ....models.models import AgendaItem
from ...generics.update import UpdateAction
from ...mixins.singular_action_mixin import SingularActionMixin
from ...mixins.tree_sort_mixin import TreeSortMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("agenda_item.sort")
class AgendaItemSort(TreeSortMixin, SingularActionMixin, UpdateAction):
    """
    Action to sort agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_tree_sort_schema()

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        yield from self.sort_tree(
            nodes=instance["tree"],
            meeting_id=instance["meeting_id"],
            weight_key="weight",
            parent_id_key="parent_id",
            children_ids_key="child_ids",
            set_level=True,
        )
