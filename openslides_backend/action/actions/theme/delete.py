from ....models.models import Theme
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("theme.delete")
class ThemeDelete(DeleteAction):
    """
    Action to delete a theme.
    """

    model = Theme()
    schema = DefaultSchema(Theme()).get_delete_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
