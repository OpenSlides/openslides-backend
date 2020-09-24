from ...models.motion_category import MotionCategory
from ...shared.schema import schema_version
from ..action import register_action
from ..base import Action, ActionPayload, DataSet
from ..sort_generic import TreeSortMixin, sort_node_schema

sort_motion_category_schema = {
    "$schema": schema_version,
    "title": "Sort motions schema",
    "description": "Meeting id and an array of motions to be sorted.",
    "type": "object",
    "properties": {
        "meeting_id": MotionCategory().get_schema("meeting_id"),
        "nodes": {
            "description": (
                "An array of motions to be sorted. The array should contain all "
                "root motions of a meeting. Each node is a dictionary with an id "
                "and optional children. In the end all motions of a meeting should "
                "appear."
            ),
            "type": "array",
            "items": sort_node_schema,
            "minItems": 1,
            "uniqueItems": True,
        },
    },
    "required": ["meeting_id", "nodes"],
    "additionalProperties": False,
}


@register_action("motion_category.sort")
class MotionCategorySort(TreeSortMixin, Action):
    """
    Action to sort motion categories.
    """

    model = MotionCategory()
    schema = sort_motion_category_schema

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
