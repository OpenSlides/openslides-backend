import time
from typing import Any

from ....models.models import Mediafile, MeetingMediafile
from ....permissions.permissions import Permissions
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..meeting_mediafile.create import MeetingMediafileCreate
from .calculate_mixins import calculate_inherited_groups_helper_with_parent_id
from .mixins import MediafileCreateMixin


@register_action("mediafile.create_directory")
class MediafileCreateDirectory(MediafileCreateMixin, CreateAction):
    """
    Action to create directory a mediafile.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_create_schema(
        required_properties=["owner_id", "title"],
        optional_properties=["parent_id", "is_published_to_meetings"],
        additional_optional_fields={
            "access_group_ids": MeetingMediafile.access_group_ids.get_schema()
        },
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
        collection, meeting_id = self.get_owner_data(instance)
        if collection == "meeting":
            mm_instance: dict[str, Any] = {
                "meeting_id": meeting_id,
                "mediafile_id": instance["id"],
            }
            if "access_group_ids" in instance:
                mm_instance["access_group_ids"] = instance.pop("access_group_ids")
            (
                mm_instance["is_public"],
                mm_instance["inherited_access_group_ids"],
            ) = calculate_inherited_groups_helper_with_parent_id(
                self.datastore,
                mm_instance.get("access_group_ids"),
                instance.get("parent_id"),
                meeting_id,
            )
            self.execute_other_action(MeetingMediafileCreate, [mm_instance])
        return instance
