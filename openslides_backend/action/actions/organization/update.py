from typing import Any, Dict

from ....models.models import Organization
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....shared.exceptions import MissingPermission
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("organization.update")
class OrganizationUpdate(UpdateAction):
    """
    Action to update a organization.
    """

    model = Organization()
    schema = DefaultSchema(Organization()).get_update_schema(
        optional_properties=[
            "name",
            "description",
            "legal_notice",
            "privacy_policy",
            "login_text",
            "theme",
            "custom_translations",
            "enable_electronic_voting",
            "reset_password_verbose_errors",
        ]
    )

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        # check group A fields
        if any(
            [
                field in instance
                for field in [
                    "name",
                    "description",
                    "legal_notice",
                    "privacy_policy",
                    "login_text",
                    "theme",
                    "custom_translations",
                ]
            ]
        ) and not has_organization_management_level(
            self.datastore,
            self.user_id,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION)

        # check group B fields
        if any(
            [
                field in instance
                for field in [
                    "enable_electronic_voting",
                    "reset_password_verbose_errors",
                ]
            ]
        ) and not has_organization_management_level(
            self.datastore,
            self.user_id,
            OrganizationManagementLevel.SUPERADMIN,
        ):
            raise MissingPermission(OrganizationManagementLevel.SUPERADMIN)
