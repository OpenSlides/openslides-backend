import time
from typing import Any

from ....models.models import Mediafile
from ....permissions.permissions import Permissions
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .calculate_mixins import calculate_inherited_groups_helper_with_parent_id
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

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate inherited_access_group_ids and inherited_access_group_ids, if
        access_group_ids are given.
        """
        instance = super().update_instance(instance)
        instance["is_directory"] = True
        instance["create_timestamp"] = round(time.time())
        collection, id_ = self.get_owner_data(instance)
        if collection == "meeting":
            (
                instance["is_public"],
                instance["inherited_access_group_ids"],
            ) = calculate_inherited_groups_helper_with_parent_id(
                self.datastore,
                instance.get("access_group_ids"),
                instance.get("parent_id"),
            )
        else:
            instance["is_public"] = True
        return instance
