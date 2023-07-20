from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ...util.register import register_action
from .base_json_upload import BaseUserJsonUpload
from openslides_backend.shared.schema import required_id_schema, str_list_schema


@register_action("participant.json_upload")
class ParticipantJsonUpload(BaseUserJsonUpload):
    schema = BaseUserJsonUpload.get_schema(
        additional_required_fields={
            "meeting_id": required_id_schema,
        },
        additional_user_fields={
            **User().get_properties(
                "structure_level",
                "number",
                "vote_weight",
                "comment",
            ),
            "is_present": {"type": "boolean"},
            "groups": str_list_schema,
        },
    )
    headers = BaseUserJsonUpload.headers + [
        {"property": "structure_level", "type": "string"},
        {"property": "number", "type": "string"},
        {"property": "vote_weight", "type": "decimal"},
        {"property": "comment", "type": "string"},
        {"property": "is_present", "type": "boolean"},
        {"property": "groups", "type": "string", "is_object": True, "is_list": True},
    ]
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS
