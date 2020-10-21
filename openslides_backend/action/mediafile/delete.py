from typing import Any, Dict, Iterable, List

from ...models.models import Mediafile
from ...shared.patterns import Collection, FullQualifiedId
from ..base import ActionPayload
from ..default_schema import DefaultSchema
from ..generics import DeleteAction
from ..register import register_action


@register_action("mediafile.delete")
class MediafileDelete(DeleteAction):
    """
    Action to delete a user.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_delete_schema()

    def get_updated_instances(self, payload: ActionPayload) -> Iterable[Dict[str, Any]]:
        new_payload = []
        for instance in payload:
            new_payload.extend(
                [{"id": id_} for id_ in self.get_tree_ids(instance["id"])]
            )
        return new_payload

    def get_tree_ids(self, id_: int) -> List[int]:
        tree_ids = [id_]
        node = self.database.get(
            FullQualifiedId(Collection("mediafile"), id_), ["child_ids"]
        )
        if node.get("child_ids"):
            for child_id in node["child_ids"]:
                tree_ids.extend(self.get_tree_ids(child_id))
        return tree_ids
