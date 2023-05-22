from typing import Any, Dict, Optional, cast

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import Organization
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.filters import FilterOperator
from ...generics.update import UpdateAction
from ...mixins.send_email_mixin import EmailCheckMixin, EmailSenderCheckMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("organization.update")
class OrganizationUpdate(
    EmailCheckMixin, EmailSenderCheckMixin, UpdateAction, CheckForArchivedMeetingMixin
):
    """
    Action to update a organization.
    """

    group_A_fields = (
        "name",
        "description",
        "legal_notice",
        "privacy_policy",
        "login_text",
        "theme_id",
        "default_language",
        "users_email_sender",
        "users_email_replyto",
        "users_email_subject",
        "users_email_body",
    )

    group_B_fields = (
        "enable_electronic_voting",
        "enable_chat",
        "reset_password_verbose_errors",
        "limit_of_meetings",
        "limit_of_users",
        "url",
        "sso_enabled",
        "sso_login_button_text",
        "sso_attr_mapping",
    )

    model = Organization()
    schema = DefaultSchema(Organization()).get_update_schema(
        optional_properties=group_A_fields + group_B_fields,
        additional_optional_fields={"sso_attr_mapping": {"type": "object"}},
    )
    check_email_field = "users_email_replyto"

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if any(
            [field in instance for field in OrganizationUpdate.group_A_fields]
        ) and not has_organization_management_level(
            self.datastore,
            self.user_id,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION)

        if any(
            [field in instance for field in OrganizationUpdate.group_B_fields]
        ) and not has_organization_management_level(
            self.datastore,
            self.user_id,
            OrganizationManagementLevel.SUPERADMIN,
        ):
            raise MissingPermission(OrganizationManagementLevel.SUPERADMIN)

    def validate_instance(self, instance: Dict[str, Any]) -> None:
        super().validate_instance(instance)
        if "sso_attr_mapping" in instance:
            sso_attr_mapping: Optional[Dict] = instance["sso_attr_mapping"]
            if "saml_id" not in cast(Dict[Any, Any], sso_attr_mapping).values():
                raise ActionException(
                    "sso_attr_mapping must contain the OpenSlides field 'saml_id'"
                )
        return super().validate_instance(instance)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        organization_id = instance.get("id", 0)
        if limit_of_meetings := instance.get("limit_of_meetings"):
            organization = self.datastore.get(
                ONE_ORGANIZATION_FQID,
                ["active_meeting_ids"],
            )

            if (
                count_active_meetings := len(organization.get("active_meeting_ids", []))
            ) > limit_of_meetings:
                raise ActionException(
                    f"Organization {organization_id} has {count_active_meetings} active meetings. You cannot set the limit lower."
                )

        if limit_of_users := instance.get("limit_of_users"):
            filter_ = FilterOperator("is_active", "=", True)
            count_active_users = self.datastore.count("user", filter_)
            if count_active_users > limit_of_users:
                raise ActionException(
                    f"Active users: {count_active_users}. You cannot set the limit lower."
                )
        return instance
