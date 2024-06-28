import re
from typing import Any

from openslides_backend.permissions.permissions import Permissions

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import ActionException, PermissionException
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import optional_id_schema
from ...generics.update import UpdateAction
from ...mixins.send_email_mixin import EmailCheckMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .conditional_speaker_cascade_mixin import ConditionalSpeakerCascadeMixin
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .user_mixins import (
    LimitOfUserMixin,
    UpdateHistoryMixin,
    UserMixin,
    check_gender_exists,
)


@register_action("user.update")
class UserUpdate(
    EmailCheckMixin,
    CreateUpdatePermissionsMixin,
    UpdateAction,
    LimitOfUserMixin,
    UpdateHistoryMixin,
    ConditionalSpeakerCascadeMixin,
):
    """
    Action to update a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        optional_properties=[
            "username",
            "pronoun",
            "title",
            "first_name",
            "last_name",
            "is_active",
            "is_physical_person",
            "default_password",
            "can_change_own_password",
            "gender_id",
            "email",
            "default_vote_weight",
            "organization_management_level",
            "committee_management_ids",
            "is_demo_user",
            "saml_id",
            "member_number",
        ],
        additional_optional_fields={
            "meeting_id": optional_id_schema,
            **UserMixin.transfer_field_list,
        },
    )
    permission = Permissions.User.CAN_UPDATE
    check_email_field = "email"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        user = self.datastore.get(
            fqid_from_collection_and_id("user", instance["id"]),
            mapped_fields=[
                "is_active",
                "organization_management_level",
                "saml_id",
                "password",
            ],
        )
        if user.get("saml_id") and (
            instance.get("can_change_own_password") or instance.get("default_password")
        ):
            raise ActionException(
                f"user {user['saml_id']} is a Single Sign On user and may not set the local default_passwort or the right to change it locally."
            )
        if instance.get("saml_id") and user.get("password"):
            instance["can_change_own_password"] = False
            instance["default_password"] = ""
            instance["password"] = ""

        if instance.get("username") and re.search(r"\s", instance["username"]):
            raise ActionException("Username may not contain spaces")

        if (
            instance["id"] == self.user_id
            and user.get("organization_management_level")
            == OrganizationManagementLevel.SUPERADMIN
        ):
            if (
                "organization_management_level" in instance
                and instance.get("organization_management_level")
                != OrganizationManagementLevel.SUPERADMIN
            ):
                raise PermissionException(
                    "A user is not allowed to withdraw his own 'superadmin'-Organization-Management-Level."
                )
            if "is_active" in instance and instance.get("is_active") is not True:
                raise PermissionException(
                    "A superadmin is not allowed to set himself inactive."
                )
        if instance.get("is_active") and not user.get("is_active"):
            self.check_limit_of_user(1)

        check_gender_exists(self.datastore, instance)
        return instance

    def get_removed_meeting_id(self, instance: dict[str, Any]) -> int | None:
        if instance.get("group_ids") == []:
            return instance.get("meeting_id")
        return None
