from typing import Any, Dict

from ....models.helper import calculate_inherited_groups_helper
from ....models.models import Mediafile
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator, Not
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .calculate_mixins import MediafileCalculatedFieldsMixin
from .permission_mixin import MediafilePermissionMixin


@register_action("mediafile.update")
class MediafileUpdate(
    MediafilePermissionMixin, UpdateAction, MediafileCalculatedFieldsMixin
):
    """
    Action to update a mediafile.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_update_schema(
        optional_properties=["title", "access_group_ids", "token"]
    )
    permission = Permissions.Mediafile.CAN_MANAGE

    def get_updated_instances(self, instances: ActionData) -> ActionData:
        """
        Calculate access_group_ids and inherited_access_group_ids, if
        access_group_ids are given.
        """
        for instance in instances:
            if instance.get("access_group_ids") is None:
                yield instance
                continue
            mediafile = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["parent_id"]
            )
            if mediafile.get("parent_id"):
                parent = self.datastore.get(
                    FullQualifiedId(self.model.collection, mediafile["parent_id"]),
                    ["is_public", "inherited_access_group_ids", "is_directory"],
                )
                if parent.get("is_directory") is not True:
                    raise ActionException("Cannot have a non-directory parent.")

                (
                    instance["is_public"],
                    instance["inherited_access_group_ids"],
                ) = calculate_inherited_groups_helper(
                    instance["access_group_ids"],
                    parent.get("is_public"),
                    parent.get("inherited_access_group_ids"),
                )
            else:
                instance["inherited_access_group_ids"] = instance["access_group_ids"]
                instance["is_public"] = not bool(instance["inherited_access_group_ids"])

            yield instance

            # Handle children
            yield from self.handle_children(
                instance,
                instance["is_public"],
                instance["inherited_access_group_ids"],
            )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if instance.get("title"):
            mediafile = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["parent_id"]
            )
            filter_ = And(
                FilterOperator("title", "=", instance["title"]),
                FilterOperator("parent_id", "=", mediafile.get("parent_id")),
                Not(FilterOperator("id", "=", instance["id"])),
            )
            results = self.datastore.filter(self.model.collection, filter_, ["id"])
            if results:
                raise ActionException(
                    f"Title '{instance['title']}' and parent_id '{mediafile.get('parent_id')}' are not unique."
                )
        if instance.get("access_group_ids"):
            collection, id_ = self.get_owner_data(instance)
            gm_request = GetManyRequest(
                Collection("group"),
                instance["access_group_ids"],
                ["id", "meeting_id"],
            )
            gm_result = self.datastore.get_many([gm_request])
            groups = gm_result[Collection("group")].values()
            for group in groups:
                if group.get("meeting_id") != id_:
                    raise ActionException("Owner and access groups don't match.")
        if instance.get("token"):
            filter_ = And(
                FilterOperator("token", "=", instance["token"]),
                Not(FilterOperator("id", "=", instance["id"])),
            )
            results = self.datastore.filter(self.model.collection, filter_, ["id"])
            if results:
                raise ActionException(f"Token '{instance['token']}' is not unique.")

        return instance
