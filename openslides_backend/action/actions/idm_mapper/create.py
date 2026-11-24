from typing import Any

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import IdmMapper
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ....shared.util import ONE_ORGANIZATION_ID


@register_action("idm_mapper.create")
class IdmMapperCreate(CreateAction, CheckForArchivedMeetingMixin):
    """
    Action to create idm_mapper.
    """

    model = IdmMapper()
    schema = DefaultSchema(IdmMapper()).get_create_schema(
        required_properties=["group_external_ids"],
        optional_properties=["weight"]
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance["organization_id"] = ONE_ORGANIZATION_ID
        return instance
