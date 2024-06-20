from ....models.models import Speaker
from ....permissions.management_levels import OrganizationManagementLevel
from ...action import ActionType
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("speaker.create_for_merge", action_type=ActionType.BACKEND_INTERNAL)
class SpeakerCreateForMerge(CreateActionWithInferredMeeting):
    model = Speaker()
    relation_field_for_meeting = "list_of_speakers_id"
    schema = DefaultSchema(Speaker()).get_create_schema(
        required_properties=["list_of_speakers_id", "meeting_user_id", "weight"],
        optional_properties=[
            i
            for i in Speaker.__dict__.keys()
            if i[:1] != "_"
            and i
            not in [
                "collection",
                "verbose_name",
                "id",
                "list_of_speakers_id",
                "meeting_user_id",
                "weight",
                "meeting_id",
                "pause_time",
            ]
        ],
    )
    permission = permission = OrganizationManagementLevel.CAN_MANAGE_USERS
