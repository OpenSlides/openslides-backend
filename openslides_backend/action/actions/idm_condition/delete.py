from ....models.models import IdmCondition
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("idm_condition.delete")
class IdmConditionDelete(DeleteAction):
    """
    Action to delete idm_condition.
    """

    model = IdmCondition()
    schema = DefaultSchema(IdmCondition()).get_delete_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
