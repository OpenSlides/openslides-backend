from typing import Any, Dict

from ....models.models import Organization
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.patterns import Collection, FullQualifiedId
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
            "default_theme_id",
            "enable_electronic_voting",
            "reset_password_verbose_errors",
            "limit_of_meetings",
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
                    "default_theme_id",
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
                    "limit_of_meetings",
                ]
            ]
        ) and not has_organization_management_level(
            self.datastore,
            self.user_id,
            OrganizationManagementLevel.SUPERADMIN,
        ):
            raise MissingPermission(OrganizationManagementLevel.SUPERADMIN)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        organization_id = instance.get("id", 0)
        if limit_of_meetings := instance.get("limit_of_meetings"):
            organization = self.datastore.get(
                FullQualifiedId(Collection("organization"), organization_id),
                ["active_meeting_ids"],
            )

            if (
                count_active_meetings := len(organization.get("active_meeting_ids", []))
            ) > limit_of_meetings:
                raise ActionException(
                    f"Organization {organization_id} has {count_active_meetings} active meetings. You cannot set the limit lower."
                )
        return instance
