from typing import Any, Dict

from ...models.models import Mediafile
from ...shared.patterns import FullQualifiedId
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action
from .calculate_mixins import MediafileCalculatedFieldsMixin


@register_action("mediafile.create_directory")
class MediafileUpdate(MediafileCalculatedFieldsMixin, CreateAction):
    """
    Action to create directory a mediafile.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_create_schema(
        required_properties=["meeting_id", "title"],
        optional_properties=["access_group_ids", "parent_id"],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate inherited_access_group_ids and inherited_access_group_ids, if
        access_group_ids are given.
        """
        instance["is_directory"] = True
        if instance.get("parent_id") is not None:
            parent = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["parent_id"]),
                ["is_public", "inherited_access_group_ids"],
            )

            (
                instance["is_public"],
                instance["inherited_access_group_ids"],
            ) = self.calculate_inherited_groups(
                instance["access_group_ids"],
                parent.get("is_public"),
                parent.get("inherited_access_group_ids"),
            )
        else:
            instance["inherited_access_group_ids"] = instance["access_group_ids"]
            instance["is_public"] = not bool(instance["inherited_access_group_ids"])
        return instance
