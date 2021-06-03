from ....models.models import OrganizationTag
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("organization_tag.create")
class OrganizationTagCreate(CreateAction):
    """
    Action to create an organization tag.
    """

    model = OrganizationTag()
    schema = DefaultSchema(OrganizationTag()).get_create_schema(
        required_properties=["name", "color", "organization_id"]
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANISATION
