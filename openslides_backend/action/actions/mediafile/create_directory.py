import time
from typing import Any, Dict

from ....models.helper import calculate_inherited_groups_helper
from ....models.models import Mediafile
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .permission_mixin import MediafilePermissionMixin


@register_action("mediafile.create_directory")
class MediafileCreateDirectory(MediafilePermissionMixin, CreateAction):
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

        # check parent (is_dir and owner)
        if instance.get("parent_id"):
            parent = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["parent_id"]),
                ["is_directory", "owner_id"],
            )
            if not parent.get("is_directory"):
                raise ActionException("Parent is not a directory.")
            if parent.get("owner_id") != str(instance["owner_id"]):
                raise ActionException("Owner and parent don't match.")

        # check (title, parent_id) unique
        filter_ = And(
            FilterOperator("title", "=", instance["title"]),
            FilterOperator("parent_id", "=", instance.get("parent_id")),
        )
        results = self.datastore.filter(self.model.collection, filter_, ["id"])
        if results:
            raise ActionException(
                f"Title '{instance['title']}' and parent_id '{instance.get('parent_id')}' are not unique."
            )

        # check access groups and owner
        if instance.get("access_group_ids"):
            collection, ids_ = self.get_owner_data(instance)
            gm_request = GetManyRequest(
                Collection("group"), instance["access_group_ids"], ["meeting_id"]
            )
            gm_result = self.datastore.get_many([gm_request])
            groups = gm_result.get(Collection("group"), {}).values()
            for group in groups:
                if group.get("meeting_id") != id_:
                    raise ActionException("Owner and access groups don't match.")

        return instance
