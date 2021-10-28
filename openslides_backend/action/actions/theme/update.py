from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import Theme
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import THEME_OPT_FIELDS, THEME_REQ_FIELDS


@register_action("theme.update")
class ThemeUpdate(UpdateAction, CheckForArchivedMeetingMixin):
    """
    Action to update an theme.
    """

    model = Theme()
    schema = DefaultSchema(Theme()).get_update_schema(
        optional_properties=(THEME_REQ_FIELDS + THEME_OPT_FIELDS)
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
