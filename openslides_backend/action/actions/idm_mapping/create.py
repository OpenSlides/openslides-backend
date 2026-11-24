from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import IdmMapping
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("idm_mapping.create")
class IdmMappingCreate(CreateAction, CheckForArchivedMeetingMixin):
    """
    Action to create idm_mapping.
    """

    model = IdmMapping()
    schema = DefaultSchema(IdmMapping()).get_create_schema(
        required_properties=["idm_field", "os_field", "mapper_id"],
        optional_properties=["default_value", "allow_update", "override_default"],
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
