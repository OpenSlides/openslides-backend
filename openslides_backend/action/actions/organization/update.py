from typing import Any, Dict

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import Organization
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.filters import FilterOperator, Or
from ....shared.schema import optional_str_schema
from ...generics.update import UpdateAction
from ...mixins.send_email_mixin import EmailCheckMixin, EmailSenderCheckMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..user.save_saml_account import allowed_user_fields
from ..user.update import UserUpdate


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
        "genders",
    )

    group_B_fields = (
        "enable_electronic_voting",
        "enable_chat",
        "reset_password_verbose_errors",
        "limit_of_meetings",
        "limit_of_users",
        "url",
        "saml_enabled",
        "saml_login_button_text",
        "saml_attr_mapping",
        "saml_metadata_idp",
        "saml_metadata_sp",
        "saml_private_key",
    )

    model = Organization()
    schema = DefaultSchema(Organization()).get_update_schema(
        optional_properties=group_A_fields + group_B_fields,
        additional_optional_fields={
            "saml_attr_mapping": {
                "type": ["object", "null"],
                "properties": {
                    field: {**optional_str_schema, "max_length": 256}
                    for field in allowed_user_fields
                },
                "required": ["saml_id"],
                "additionalProperties": False,
            },
        },
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        if limit_of_meetings := instance.get("limit_of_meetings"):
            organization = self.datastore.get(
                ONE_ORGANIZATION_FQID,
                ["active_meeting_ids"],
            )

            if (
                count_active_meetings := len(organization.get("active_meeting_ids", []))
            ) > limit_of_meetings:
                raise ActionException(
                    f"Your organization has {count_active_meetings} active meetings. You cannot set the limit lower."
                )

        if limit_of_users := instance.get("limit_of_users"):
            filter_ = FilterOperator("is_active", "=", True)
            count_active_users = self.datastore.count("user", filter_)
            if count_active_users > limit_of_users:
                raise ActionException(
                    f"Active users: {count_active_users}. You cannot set the limit lower."
                )
        if "genders" in instance:
            organization = self.datastore.get(ONE_ORGANIZATION_FQID, ["genders"])
            removed_genders = [
                gender
                for gender in organization.get("genders", [])
                if gender not in instance["genders"]
            ]

            if removed_genders:
                filter__ = Or(
                    *[
                        FilterOperator("gender", "=", gender)
                        for gender in removed_genders
                    ]
                )
                users = self.datastore.filter("user", filter__, ["id"]).values()
                payload_remove_gender = [
                    {"id": entry["id"], "gender": None} for entry in users
                ]
                if payload_remove_gender:
                    self.execute_other_action(UserUpdate, payload_remove_gender)
        return instance
