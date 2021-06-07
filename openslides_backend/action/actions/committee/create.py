from ....models.models import Committee
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("committee.create")
class CommitteeCreate(CreateAction):
    """
    Action to create committees.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_create_schema(
        required_properties=["organization_id", "name"],
        optional_properties=["description", "user_ids", "organization_tag_ids"],
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
