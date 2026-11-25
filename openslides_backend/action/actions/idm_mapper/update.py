from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import IdmMapper
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("idm_mapper.update")
class IdmMapperUpdate(UpdateAction, CheckForArchivedMeetingMixin):
    """
    Action to update idm_mapper.
    """

    model = IdmMapper()
    schema = DefaultSchema(IdmMapper()).get_update_schema(
        required_properties=["group_external_ids"]
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
