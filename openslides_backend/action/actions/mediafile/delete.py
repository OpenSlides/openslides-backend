from ....models.models import Mediafile
from ....permissions.permissions import Permissions
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import MediafileMixin


@register_action("mediafile.delete")
class MediafileDelete(MediafileMixin, DeleteAction):
    """
    Action to delete a user.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_delete_schema()
    permission = Permissions.Mediafile.CAN_MANAGE
    is_delete_action = True

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            yield from ({"id": id_} for id_ in self.get_tree_ids(instance["id"]))

    def get_tree_ids(self, id_: int) -> list[int]:
        tree_ids = [id_]
        node = self.datastore.get(
            fqid_from_collection_and_id("mediafile", id_), ["child_ids"]
        )
        if node.get("child_ids"):
            for child_id in node["child_ids"]:
                if not self.is_deleted(
                    fqid_from_collection_and_id("mediafile", child_id)
                ):
                    tree_ids.extend(self.get_tree_ids(child_id))
        return tree_ids
