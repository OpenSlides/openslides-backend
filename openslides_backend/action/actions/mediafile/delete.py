from typing import List

from ....models.models import Mediafile
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("mediafile.delete")
class MediafileDelete(DeleteAction):
    """
    Action to delete a user.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_delete_schema()

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            yield from ({"id": id_} for id_ in self.get_tree_ids(instance["id"]))

    def get_tree_ids(self, id_: int) -> List[int]:
        tree_ids = [id_]
        node = self.datastore.get(
            FullQualifiedId(Collection("mediafile"), id_), ["child_ids"]
        )
        if node.get("child_ids"):
            for child_id in node["child_ids"]:
                tree_ids.extend(self.get_tree_ids(child_id))
        return tree_ids
