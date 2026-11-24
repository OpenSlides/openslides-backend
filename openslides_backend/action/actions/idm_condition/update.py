from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import IdmCondition
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("idm_condition.update")
class IdmConditionUpdate(CreateAction, CheckForArchivedMeetingMixin):
    """
    Action to update idm_condition.
    """

    model = IdmCondition()
    schema = DefaultSchema(IdmCondition()).get_update_schema(
        optional_properties=["idm_field", "regex", "mapper_id"]
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
