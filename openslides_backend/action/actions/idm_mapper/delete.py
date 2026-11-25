from ....models.models import IdmMapper
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("idm_mapper.delete")
class IdmMapperDelete(DeleteAction):
    """
    Action to delete idm_mapper.
    """

    model = IdmMapper()
    schema = DefaultSchema(IdmMapper()).get_delete_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
