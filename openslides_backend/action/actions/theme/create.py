from ....models.models import Theme
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("theme.create")
class ThemeCreate(CreateAction):
    """
    Action to create an theme.
    """

    model = Theme()
    schema = DefaultSchema(Theme()).get_create_schema(
        required_properties=["name", "primary_500", "accent_500", "warn_500"],
        optional_properties=[
            "primary_50",
            "primary_100",
            "primary_200",
            "primary_300",
            "primary_400",
            "primary_600",
            "primary_700",
            "primary_800",
            "primary_900",
            "primary_A100",
            "primary_A200",
            "primary_A400",
            "primary_A700",
            "accent_50",
            "accent_100",
            "accent_200",
            "accent_300",
            "accent_400",
            "accent_600",
            "accent_700",
            "accent_800",
            "accent_900",
            "accent_A100",
            "accent_A200",
            "accent_A400",
            "accent_A700",
            "warn_50",
            "warn_100",
            "warn_200",
            "warn_300",
            "warn_400",
            "warn_600",
            "warn_700",
            "warn_800",
            "warn_900",
            "warn_A100",
            "warn_A200",
            "warn_A400",
            "warn_A700",
        ],
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
