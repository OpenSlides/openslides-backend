from ...models.agenda_item import AgendaItem
from ...shared.schema import schema_version
from ..action import register_action
from ..base import Action, ActionPayload, DataSet
from ..sort_generic import TreeSortMixin, sort_node_schema

sort_agenda_item_schema = {
    "$schema": schema_version,
    "title": "Sort agenda items schema",
    "description": "Meeting id and an array of agenda items to be sorted.",
    "type": "object",
    "properties": {
        "meeting_id": AgendaItem().get_schema("meeting_id"),
        "tree": {
            "description": (
                "An array of agenda items to be sorted. The array should contain all "
                "root agenda items of a meeting. Each node is a dictionary with an id "
                "and optional children. In the end all agenda items of a meeting should "
                "appear."
            ),
            "type": "array",
            "items": sort_node_schema,
            "minItems": 1,
            "uniqueItems": True,
        },
    },
    "required": ["meeting_id", "tree"],
    "additionalProperties": False,
}


@register_action("agenda_item.sort")
class AgendaItemSort(TreeSortMixin, Action):
    """
    Action to sort agenda items.
    """

    model = AgendaItem()
    schema = sort_agenda_item_schema

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
