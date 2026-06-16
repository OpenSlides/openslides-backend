from ....action.util.typing import ActionData, ActionResults
from ....models.models import Theme
from ....permissions.management_levels import OrganizationManagementLevel
from ...ddaction import DDAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import THEME_OPT_FIELDS, THEME_REQ_FIELDS


@register_action("theme.update")
class ThemeUpdate(DDAction):
    """
    Action to update an theme.
    """

    model = Theme()
    schema = DefaultSchema(Theme()).get_update_schema(
        optional_properties=(THEME_REQ_FIELDS + THEME_OPT_FIELDS)
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True

    def write_instances(self, action_data: ActionData) -> ActionResults | None:
        return list(
            self.database.update_models(
                self.model.collection,
                list(action_data),
                [*THEME_REQ_FIELDS, *THEME_OPT_FIELDS],
            )
        )
