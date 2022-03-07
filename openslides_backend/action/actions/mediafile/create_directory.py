import time
from typing import Any, Dict

from ....models.helper import calculate_inherited_groups_helper
from ....models.models import Mediafile
from ....permissions.permissions import Permissions
from ....shared.patterns import FullQualifiedId
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import MediafileMixin


@register_action("mediafile.create_directory")
class MediafileCreateDirectory(MediafileMixin, CreateAction):
    """
    Action to create directory a mediafile.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_create_schema(
        required_properties=["owner_id", "title"],
        optional_properties=["access_group_ids", "parent_id"],
    )
    permission = Permissions.Mediafile.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate inherited_access_group_ids and inherited_access_group_ids, if
        access_group_ids are given.
        """
        instance["is_directory"] = True
        instance["create_timestamp"] = round(time.time())
        collection, id_ = self.get_owner_data(instance)
        if collection == "meeting":
            if instance.get("parent_id") is not None:
                parent = self.datastore.get(
                    FullQualifiedId(self.model.collection, instance["parent_id"]),
                    ["is_public", "inherited_access_group_ids"],
                )

                (
                    instance["is_public"],
                    instance["inherited_access_group_ids"],
                ) = calculate_inherited_groups_helper(
                    instance.get("access_group_ids"),
                    parent.get("is_public"),
                    parent.get("inherited_access_group_ids"),
                )
            else:
                instance["inherited_access_group_ids"] = instance.get(
                    "access_group_ids"
                )
                instance["is_public"] = not bool(instance["inherited_access_group_ids"])
        return instance
