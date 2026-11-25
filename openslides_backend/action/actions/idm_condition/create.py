from ....models.models import IdmCondition
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("idm_condition.create")
class IdmConditionCreate(CreateAction):
    """
    Action to create idm_condition.
    """

    model = IdmCondition()
    schema = DefaultSchema(IdmCondition()).get_create_schema(
        required_properties=["idm_field", "regex", "mapper_id"],
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
