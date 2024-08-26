from typing import Any

from openslides_backend.shared.exceptions import ActionException

from ....models.models import MeetingMediafile
from ....shared.patterns import KEYSEPARATOR, fqid_from_collection_and_id
from ...generics.create import CreateAction
from ...mixins.meeting_mediafile_helper import get_meeting_mediafile_filter
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_mediafile.create", action_type=ActionType.BACKEND_INTERNAL)
class MeetingMediafileCreate(CreateAction):
    """
    Action to create a meeting mediafile.
    This only adds data, calculations will have to be done in calling class.
    """

    model = MeetingMediafile()
    schema = DefaultSchema(MeetingMediafile()).get_create_schema(
        required_properties=["meeting_id", "mediafile_id", "is_public"],
        optional_properties=["access_group_ids", "inherited_access_group_ids"],
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        mediafile = self.datastore.get(
            fqid_from_collection_and_id("mediafile", instance["mediafile_id"]),
            ["owner_id", "published_to_meetings_in_organization_id"],
        )
        if mediafile["owner_id"].split(KEYSEPARATOR)[
            0
        ] == "organization" and not mediafile.get(
            "published_to_meetings_in_organization_id"
        ):
            raise ActionException(
                "Mediafile is neither a meeting mediafile nor published."
            )
        if self.datastore.exists(
            "meeting_mediafile",
            get_meeting_mediafile_filter(
                instance["meeting_id"], instance["mediafile_id"]
            ),
        ):
            raise ActionException(
                f"MeetingMediafile instance with mediafile {instance['mediafile_id']} and meeting {instance['meeting_id']} already exists"
            )
        return super().update_instance(instance)
