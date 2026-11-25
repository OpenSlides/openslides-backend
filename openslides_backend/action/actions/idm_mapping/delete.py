from ....models.models import IdmMapping
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("idm_mapping.delete")
class IdmMappingDelete(DeleteAction):
    """
    Action to delete idm_mapping.
    """

    model = IdmMapping()
    schema = DefaultSchema(IdmMapping()).get_delete_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
