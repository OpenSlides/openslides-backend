from typing import Any

import fastjsonschema

from ...shared.exceptions import ActionException
from ...shared.filters import FilterOperator
from ..action import Action
from ..util.default_schema import sort_node_schema
from ..util.typing import ActionData

validate_sort_node = fastjsonschema.compile(sort_node_schema)


class TreeSortMixin(Action):
    """
    Provides an action mixin for sorting a model tree.
    """

    def sort_tree(
        self,
        nodes: list,
        meeting_id: int,
        weight_key: str,
        parent_id_key: str,
        children_ids_key: str,
        set_level: bool = False,
    ) -> ActionData:
        """
        Sorts the all model objects represented in a tree of ids. The request
        data should be a list (the root) of all main models. Each node is a dict
        with an id and optional children. Every id has to be given.

        This function traverses this tree in preorder to assign the weight.
        """
        # TODO: Check if instances exist in DB and is not deleted. Ensure that meta_deleted field is added to locked_fields.

        # Get all item ids to verify, that the user send all ids.
        filter = FilterOperator("meeting_id", "=", meeting_id)
        db_instances = self.datastore.filter(
            collection=self.model.collection,
            filter=filter,
            mapped_fields=["id"],
        )
        all_model_ids = set(db_instances.keys())

        # Setup initial node using a fake root node.
        fake_root: dict[str, Any] = {"id": None, "children": []}
        fake_root["children"].extend(nodes)  # This will prevent mutating the nodes.

        # The stack where all nodes to check are saved. Invariant: Each node
        # must be a dict with an id, a parent id (may be None for the root
        # layer) and a weight.
        nodes_to_check = [fake_root]

        # Traverse and check if every id is given, valid and there are no duplicate ids.
        ids_found: set[int] = set()  # Set to save all found ids.
        nodes_to_update: dict[int, dict[str, Any]] = {}  # Result data.

        # Now walk through the tree.
        while len(nodes_to_check) > 0:
            node = nodes_to_check.pop()
            id = node["id"]

            if id is not None:  # Exclude the fake_root
                # Parse current node.
                nodes_to_update[id] = {}
                nodes_to_update[id]["id"] = id
                nodes_to_update[id][children_ids_key] = []
                parent_id = node.get(parent_id_key)
                nodes_to_update[id][parent_id_key] = parent_id
                if parent_id is not None:
                    nodes_to_update[parent_id][children_ids_key].append(id)
                nodes_to_update[id][weight_key] = node[weight_key]

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
                weight = len(node["children"])
                for child in node["children"]:
                    validate_sort_node(child)
                    child[parent_id_key] = id
                    nodes_to_check.append(child)
                    child[weight_key] = weight
                    weight -= 1

        # Check if all ids are used.
        if len(all_model_ids) != len(ids_found):
            raise ActionException(
                f"Did not recieve {len(all_model_ids)} ids, got {len(ids_found)}."
            )
        if set_level:
            self.set_level_main(nodes_to_update, parent_id_key)

        yield from nodes_to_update.values()

    def set_level_main(
        self, nodes_to_update: dict[int, dict[str, Any]], parent_id_key: str
    ) -> None:
        for id_ in nodes_to_update:
            self.set_level_helper(id_, nodes_to_update, parent_id_key)

    def set_level_helper(
        self, id_: int, nodes_to_update: dict[int, dict[str, Any]], parent_id_key: str
    ) -> None:
        if nodes_to_update[id_][parent_id_key] is None:
            nodes_to_update[id_]["level"] = 0
        else:
            parent_id = nodes_to_update[id_][parent_id_key]
            if nodes_to_update[parent_id].get("level") is None:
                self.set_level_helper(parent_id, nodes_to_update, parent_id_key)
            nodes_to_update[id_]["level"] = nodes_to_update[parent_id]["level"] + 1
