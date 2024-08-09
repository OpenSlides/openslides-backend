from ....models.models import Mediafile, MeetingMediafile
from ....permissions.permissions import Permissions
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .calculate_mixins import (
    MediafileCalculatedFieldsMixin,
    calculate_inherited_groups_helper_with_parent_id,
)
from .mixins import MediafileMixin


@register_action("mediafile.update")
class MediafileUpdate(MediafileMixin, UpdateAction, MediafileCalculatedFieldsMixin):
    """
    Action to update a mediafile.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_update_schema(
        optional_properties=["title", "token"],
        additional_optional_fields={
            "access_group_ids": MeetingMediafile.access_group_ids.get_schema()
        },
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
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                ["parent_id"],
            )
            (
                instance["is_public"],
                instance["inherited_access_group_ids"],
            ) = calculate_inherited_groups_helper_with_parent_id(
                self.datastore,
                instance.get("access_group_ids"),
                mediafile.get("parent_id"),
            )
            yield instance

            # Handle children
            yield from self.handle_children(
                instance,
                instance["is_public"],
                instance["inherited_access_group_ids"],
            )
