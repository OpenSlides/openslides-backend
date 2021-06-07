from ....models.models import OrganizationTag
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("organization_tag.update")
class OrganizationTagUpdate(UpdateAction):
    """
    Action to update an organization tag.
    """

    model = OrganizationTag()
    schema = DefaultSchema(OrganizationTag()).get_update_schema(
        optional_properties=["name", "color"]
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
