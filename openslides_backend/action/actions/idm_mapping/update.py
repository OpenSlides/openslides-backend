from ....models.models import IdmMapping
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("idm_mapping.update")
class IdmMappingUpdate(UpdateAction):
    """
    Action to update idm_mapping.
    """

    model = IdmMapping()
    schema = DefaultSchema(IdmMapping()).get_update_schema(
        optional_properties=[
            "idm_field",
            "default_value",
            "allow_update",
            "override_default",
        ]
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
