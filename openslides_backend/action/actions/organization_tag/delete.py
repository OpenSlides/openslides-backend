from ....models.models import OrganizationTag
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("organization_tag.delete")
class OrganizationTagDelete(DeleteAction):
    """
    Action to delete a organization tag.
    """

    model = OrganizationTag()
    schema = DefaultSchema(OrganizationTag()).get_delete_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
