from typing import Any, Dict, Iterable, List, Set

import fastjsonschema

from ..models.base import Model
from ..shared.exceptions import ActionException
from ..shared.filters import FilterOperator
from ..shared.interfaces import Event, WriteRequestElement
from ..shared.patterns import FullQualifiedId
from ..shared.schema import schema_version
from .base import Action, BaseAction, DataSet

sort_node_schema = {
    "$schema": schema_version,
    "title": "Sort node schema",
    "id": "tree_sort_node",
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
            "items": {"type": "object", "$ref": "tree_sort_node"},
            "minItems": 1,
            "uniqueItems": True,
        },
    },
    "required": ["id"],
    "additionalProperties": False,
}

validate_sort_node = fastjsonschema.compile(sort_node_schema)


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
        filter = FilterOperator("meeting_id", "=", meeting_id)
        db_instances = self.database.filter(
            collection=self.model.collection,
            filter=filter,
            mapped_fields=["id"],
            lock_result=True,
        )
        all_model_ids = set(db_instances.keys())

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


class LinearSortMixin(Action):
    """
    Provides a mixin for linear sorting.
    """

    def sort_linear(self, nodes: List, filter_id: int, filter_str: str) -> DataSet:
        filter = FilterOperator(filter_str, "=", filter_id)
        db_instances = self.database.filter(
            collection=self.model.collection,
            filter=filter,
            mapped_fields=["id"],
            lock_result=True,
        )
        valid_instance_ids = []
        for id_ in nodes:
            if id_ not in db_instances:
                raise ActionException(f"Id {id_} not in db_instances.")
            valid_instance_ids.append(id_)
        if len(valid_instance_ids) != len(db_instances):
            raise ActionException("Additional db_instances found.")

        data = dict()
        weight = 1
        for id_ in valid_instance_ids:
            data[id_] = {"weight": weight}
            weight += 1
        return {"data": data}

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
