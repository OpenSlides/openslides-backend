from typing import Any, Dict, Iterable, List, Set

import fastjsonschema  # type: ignore

from ...models.base import Model
from ...models.motion import Motion
from ...shared.exceptions import ActionException, PermissionDenied
from ...shared.filters import FilterOperator
from ...shared.interfaces import Event, WriteRequestElement
from ...shared.patterns import FullQualifiedId
from ...shared.permissions.motion import MOTION_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..base import Action, ActionPayload, BaseAction, DataSet, DummyAction

sort_node_schema = {
    "$schema": schema_version,
    "title": "Sort node schema",
    "description": "A node inside a sort tree.",
    "type": "object",
    "properties": {
        "id": {
            "description": "The id of the instance.",
            "type": "integer",
            "minimum": 1,
        },
        "children": {
            "type": "array",
            "items": {},  # TODO: Add recursive sort_node_schema here, then remove extra check in TreeSortMixin.
            "minItems": 1,
            "uniqueItems": True,
        },
    },
    "required": ["id"],
    "additionalProperties": False,
}

validate_sort_node = fastjsonschema.compile(sort_node_schema)

sort_motion_schema = fastjsonschema.compile(
    {
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
)


# TODO: Move this mixin to a generic place.
class TreeSortMixin(BaseAction):
    """
    Provides an action mixin for sorting a model tree.
    """

    model: Model

    def sort_tree(
        self,
        nodes: List,
        meeting_id: int,
        weight_key: str,
        parent_id_key: str,
        children_ids_key: str,
    ) -> DataSet:
        """
        Sorts the all model objects represented in a tree of ids. The request
        data should be a list (the root) of all main models. Each node is a dict
        with an id and optional children. Every id has to be given.

        This function traverses this tree in preorder to assign the weight.
        """
        # TODO: Check if instances exist in DB and is not deleted. Ensure that meta_deleted field is added to locked_fields.

        # Get all item ids to verify, that the user send all ids.
        filter = FilterOperator(field="meeting_id", value=meeting_id, operator="==")
        db_instances = self.database.filter(
            collection=self.model.collection,
            filter=filter,
            meeting_id=meeting_id,
            mapped_fields=["id"],
            lock_result=True,
        )
        all_model_ids = set([instance["id"] for instance in db_instances])

        # Setup initial node using a fake root node.
        fake_root: Dict[str, Any] = {"id": None, "children": []}
        fake_root["children"].extend(nodes)  # This will prevent mutating the nodes.

        # The stack where all nodes to check are saved. Invariant: Each node
        # must be a dict with an id, a parent id (may be None for the root
        # layer) and a weight.
        nodes_to_check = [fake_root]

        # Traverse and check if every id is given, valid and there are no duplicate ids.
        ids_found: Set[int] = set()  # Set to save all found ids.
        nodes_to_update: Dict[int, Dict[str, Any]] = {}  # Result data.

        # The weight values are 2, 4, 6, 8,... to "make space" between entries. This is
        # some work around for the agenda: If one creates a content object with an item
        # and gives the item's parent, than the weight can be set to the parent's one +1.
        # If multiple content objects witht he same parent are created, the ordering is not
        # guaranteed.
        weight = 0

        # Now walk through the tree.
        while len(nodes_to_check) > 0:
            node = nodes_to_check.pop()
            id = node["id"]

            if id is not None:  # Exclude the fake_root
                # Parse current node.
                weight += 2
                nodes_to_update[id] = {}
                nodes_to_update[id][children_ids_key] = []
                nodes_to_update[id][weight_key] = weight
                parent_id = node.get(parent_id_key)
                nodes_to_update[id][parent_id_key] = parent_id
                if parent_id is not None:
                    nodes_to_update[parent_id][children_ids_key].append(id)

                # Check id.
                if id in ids_found:
                    raise ActionException(f"Duplicate id in sort tree: {id}")
                if id not in all_model_ids:
                    raise ActionException(f"Id in sort tree does not exist: {id}")
                ids_found.add(id)

            # Add children if exist.
            if node.get("children"):
                node[
                    "children"
                ].reverse()  # Use reverse() because we use pop() some lines, so this is LIFO and not FIFO.
                for child in node["children"]:
                    validate_sort_node(child)
                    child[parent_id_key] = id
                    nodes_to_check.append(child)

        # Check if all ids are used.
        if len(all_model_ids) != len(ids_found):
            raise ActionException(
                f"Did not recieve {len(all_model_ids)} ids, got {len(ids_found)}."
            )

        return {"data": nodes_to_update}

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        for id, instance in dataset["data"].items():
            fqid = FullQualifiedId(self.model.collection, id)
            information = {fqid: ["Object sorted"]}
            event = Event(type="update", fqid=fqid, fields=instance)
            # TODO: Lock some fields to protect against intermediate creation of new instances but care where exactly to lock them.
            yield WriteRequestElement(
                events=[event], information=information, user_id=self.user_id
            )


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
        meeting_id = payload["meeting_id"]
        if not self.permission.has_perm(
            self.user_id, f"{meeting_id}/{MOTION_CAN_MANAGE}"
        ):
            raise PermissionDenied(
                f"User must have {MOTION_CAN_MANAGE} permission for "
                f"meeting_id {meeting_id}."
            )
        return self.sort_tree(
            nodes=payload["nodes"],
            meeting_id=meeting_id,
            weight_key="sort_weight",
            parent_id_key="sort_parent_id",
            children_ids_key="sort_children_ids",
        )


@register_action("motion.sort_in_category")
class MotionSortInCategory(DummyAction):
    pass
