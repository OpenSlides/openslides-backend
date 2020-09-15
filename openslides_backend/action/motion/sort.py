from ...models.motion import Motion
from ...shared.schema import schema_version
from ..action import register_action
from ..base import Action, ActionPayload, DataSet, DummyAction
from ..sort_generic import TreeSortMixin, sort_node_schema

sort_motion_schema = {
    "$schema": schema_version,
    "title": "Sort motions schema",
    "description": "Meeting id and an array of motions to be sorted.",
    "type": "object",
    "properties": {
        "meeting_id": Motion().get_schema("meeting_id"),
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


@register_action("motion.sort")
class MotionSort(TreeSortMixin, Action):
    """
    Action to sort motions.
    """

    model = Motion()
    schema = sort_motion_schema

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        if not isinstance(payload, dict):
            raise TypeError("ActionPayload for this action must be a dictionary.")
        return self.sort_tree(
            nodes=payload["nodes"],
            meeting_id=payload["meeting_id"],
            weight_key="sort_weight",
            parent_id_key="sort_parent_id",
            children_ids_key="sort_children_ids",
        )


@register_action("motion.sort_in_category")
class MotionSortInCategory(DummyAction):
    pass
