from typing import Any

from openslides_backend.models.fields import TimestampField

from ....models.models import Speaker
from ....permissions.management_levels import OrganizationManagementLevel
from ...action import ActionException, ActionType
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
            "begin_time",
            "end_time",
            "unpause_time",
            "total_pause",
            "point_of_order",
            "speech_state",
            "point_of_order_category_id",
            "structure_level_list_of_speakers_id",
            "note",
        ],
    )
    permission = permission = OrganizationManagementLevel.CAN_MANAGE_USERS
    timestamp_fields = [
        field.own_field_name
        for field in model.get_fields()
        if isinstance(field, TimestampField)
    ]

    def validate_fields(self, instance: dict[str, Any]) -> dict[str, Any]:
        is_point_oo: bool = instance.get("point_of_order", False)
        if is_point_oo:
            forbidden = ["speech_state"]
        else:
            forbidden = ["point_of_order_category_id", "note"]
        prefix = f"In list_of_speakers/{instance['list_of_speakers_id']}: "
        if len(found := {field for field in forbidden if field in instance}):
            raise ActionException(
                prefix
                + ("Point of order" if is_point_oo else "Normal speaker")
                + f" can not be created with field(s) {found} set"
            )
        if (begin_time := instance.get("begin_time")) is not None:
            if (end_time := instance.get("end_time")) is None:
                raise ActionException(
                    prefix + "Cannot create a running speech during merge"
                )
            if end_time < begin_time:
                raise ActionException(
                    prefix
                    + "Can not create finished speaker as the end_time is before the begin_time"
                )
        return super().validate_fields(instance)
