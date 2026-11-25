from ....models.models import IdmMapper
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("idm_mapper.update")
class IdmMapperUpdate(UpdateAction):
    """
    Action to update idm_mapper.
    """

    model = IdmMapper()
    schema = DefaultSchema(IdmMapper()).get_update_schema(
        required_properties=["group_external_ids"]
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
