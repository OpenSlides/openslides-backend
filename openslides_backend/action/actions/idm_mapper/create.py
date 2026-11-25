from ....models.models import IdmMapper
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("idm_mapper.create")
class IdmMapperCreate(CreateAction):
    """
    Action to create idm_mapper.
    """

    model = IdmMapper()
    schema = DefaultSchema(IdmMapper()).get_create_schema(
        required_properties=["group_external_ids"]
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
