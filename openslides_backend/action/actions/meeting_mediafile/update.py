from ....models.models import MeetingMediafile
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_mediafile.update", action_type=ActionType.BACKEND_INTERNAL)
class MeetingMediafileUpdate(UpdateAction):
    """
    Action to update a meeting_mediafile.
    """

    model = MeetingMediafile()
    schema = DefaultSchema(MeetingMediafile()).get_update_schema(
        optional_properties=[
            "access_group_ids",
            "inherited_access_group_ids",
            "is_public",
        ],
    )
