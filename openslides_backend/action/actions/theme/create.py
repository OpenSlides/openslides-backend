from ....action.util.typing import ActionData, ActionResults
from ....models.models import Theme
from ....permissions.management_levels import OrganizationManagementLevel
from ...ddaction import DDAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action

THEME_REQ_FIELDS = ["name", "primary_500", "accent_500", "warn_500"]
THEME_OPT_FIELDS = [
    "primary_50",
    "primary_100",
    "primary_200",
    "primary_300",
    "primary_400",
    "primary_600",
    "primary_700",
    "primary_800",
    "primary_900",
    "primary_a100",
    "primary_a200",
    "primary_a400",
    "primary_a700",
    "accent_50",
    "accent_100",
    "accent_200",
    "accent_300",
    "accent_400",
    "accent_600",
    "accent_700",
    "accent_800",
    "accent_900",
    "accent_a100",
    "accent_a200",
    "accent_a400",
    "accent_a700",
    "warn_50",
    "warn_100",
    "warn_200",
    "warn_300",
    "warn_400",
    "warn_600",
    "warn_700",
    "warn_800",
    "warn_900",
    "warn_a100",
    "warn_a200",
    "warn_a400",
    "warn_a700",
    "headbar",
    "yes",
    "no",
    "abstain",
]


@register_action("theme.create")
class ThemeCreate(DDAction):
    """
    Action to create a theme.
    """

    model = Theme()
    schema = DefaultSchema(Theme()).get_create_schema(
        required_properties=THEME_REQ_FIELDS,
        optional_properties=THEME_OPT_FIELDS,
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True

    def write_instances(self, action_data: ActionData) -> ActionResults | None:
        return list(
            self.database.insert_models(
                self.model.collection,
                list(action_data),
                [*THEME_REQ_FIELDS, *THEME_OPT_FIELDS],
            )
        )
