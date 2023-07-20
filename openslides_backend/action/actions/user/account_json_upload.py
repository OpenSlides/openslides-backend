from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ...util.register import register_action
from .base_json_upload import BaseUserJsonUpload


@register_action("account.json_upload")
class AccountJsonUpload(BaseUserJsonUpload):
    schema = BaseUserJsonUpload.get_schema(
        additional_user_fields=User().get_properties(
            "default_structure_level",
            "default_number",
            "default_vote_weight",
        ),
    )
    headers = BaseUserJsonUpload.headers + [
        {"property": "default_structure_level", "type": "string"},
        {"property": "default_number", "type": "string"},
        {"property": "default_vote_weight", "type": "decimal"},
    ]
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS
