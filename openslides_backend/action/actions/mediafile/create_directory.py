import time
from typing import Any

from ....models.models import Mediafile, MeetingMediafile
from ....permissions.permissions import Permissions
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import MediafileCreateMixin


@register_action("mediafile.create_directory")
class MediafileCreateDirectory(MediafileCreateMixin, CreateAction):
    """
    Action to create directory a mediafile.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_create_schema(
        required_properties=["owner_id", "title"],
        optional_properties=["parent_id"],
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
            self.handle_meeting_meeting_mediafile_creation(meeting_id, instance)
        else:
            self.handle_orga_meeting_mediafile_creation(instance)
        return instance
