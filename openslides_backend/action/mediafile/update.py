from typing import Any, Dict

from ...models.models import Mediafile
from ...shared.patterns import Collection, FullQualifiedId
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("mediafile.update")
class MediafileUpdate(UpdateAction):
    """
    Action to update a mediafile.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_update_schema(
        optional_properties=["title", "access_group_ids"]
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate inherited_access_group_ids and inherited_access_group_ids, if
        access_group_ids are given.
        """
        if instance.get("access_group_ids") is None:
            return instance
        mediafile = self.database.get(
            FullQualifiedId(Collection("mediafile"), instance["id"]), ["parent_id"]
        )
        if mediafile.get("parent_id") is not None:
            parent = self.database.get(
                FullQualifiedId(Collection("mediafile"), mediafile["parent_id"]),
                ["inherited_access_group_ids"],
            )
            if not parent.get("inherited_access_group_ids"):
                instance["inherited_access_group_ids"] = instance["access_group_ids"]
            elif not instance["access_group_ids"]:
                instance["inherited_access_group_ids"] = parent[
                    "inherited_access_group_ids"
                ]
            else:
                instance["inherited_access_group_ids"] = [
                    id_
                    for id_ in instance["access_group_ids"]
                    if id_ in parent["inherited_access_group_ids"]
                ]
            instance["has_inherited_access_groups"] = (
                len(instance["inherited_access_group_ids"]) > 0
                or len(parent["inherited_access_group_ids"]) > 0
            )
        else:
            instance["inherited_access_group_ids"] = instance["access_group_ids"]
            instance["has_inherited_access_groups"] = (
                len(instance["inherited_access_group_ids"]) > 0
            )

        return instance
