import re
from typing import Any

from openslides_backend.permissions.permissions import Permissions

from ....action.action import original_instances
from ....action.util.typing import ActionData
from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import ActionException, PermissionException
from ....shared.filters import And, FilterOperator, Or
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import optional_id_schema
from ...generics.update import UpdateAction
from ...mixins.send_email_mixin import EmailCheckMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .conditional_speaker_cascade_mixin import ConditionalSpeakerCascadeMixin
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .user_mixins import (
    AdminIntegrityCheckMixin,
    LimitOfUserMixin,
    UpdateHistoryMixin,
    UserMixin,
    check_gender_helper,
)


@register_action("user.update")
class UserUpdate(
    EmailCheckMixin,
    CreateUpdatePermissionsMixin,
    UpdateAction,
    LimitOfUserMixin,
    UpdateHistoryMixin,
    ConditionalSpeakerCascadeMixin,
    AdminIntegrityCheckMixin,
):
    """
    Action to update a user.
    """

    internal_id_fields = [
        "is_present_in_meeting_ids",
        "option_ids",
        "poll_candidate_ids",
        "poll_voted_ids",
        "vote_ids",
        "delegated_vote_ids",
    ]

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
            "gender",
            "email",
            "default_vote_weight",
            "organization_management_level",
            "committee_management_ids",
            "is_demo_user",
            "saml_id",
            "member_number",
            *internal_id_fields,
        ],
        additional_optional_fields={
            "meeting_id": optional_id_schema,
            **UserMixin.transfer_field_list,
        },
    )
    permission = Permissions.User.CAN_UPDATE
    check_email_field = "email"

    def validate_instance(self, instance: dict[str, Any]) -> None:
        super().validate_instance(instance)
        if not self.internal and any(
            forbidden_keys_used := {
                key for key in instance if key in self.internal_id_fields
            }
        ):
            raise ActionException(
                f"data must not contain {forbidden_keys_used} properties"
            )

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

        check_gender_helper(self.datastore, instance)
        return instance

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        self.check_meeting_admin_integrity(action_data)
        return super().get_updated_instances(action_data)

    def get_removed_meeting_id(self, instance: dict[str, Any]) -> int | None:
        if instance.get("group_ids") == []:
            return instance.get("meeting_id")
        return None

    def check_meeting_admin_integrity(self, instances: ActionData) -> None:
        instances = [
            instance
            for instance in instances
            if instance.get("meeting_id") and "group_ids" in instance
        ]
        meeting_ids_to_user_ids_to_group_ids: dict[int, dict[int, list[int]]] = {
            date["meeting_id"]: {} for date in instances
        }
        for date in instances:
            meeting_ids_to_user_ids_to_group_ids[date["meeting_id"]][date["id"]] = date[
                "group_ids"
            ]
        meetings = self.get_meeting_data_from_per_meeting_dict(
            meeting_ids_to_user_ids_to_group_ids
        )
        self.filter_templates_from_per_meeting_dict(
            meeting_ids_to_user_ids_to_group_ids, meetings
        )
        if not len(meeting_ids_to_user_ids_to_group_ids):
            return
        self.check_admin_group_integrity(
            Or(
                And(
                    FilterOperator("meeting_id", "=", meeting_id),
                    Or(
                        FilterOperator("user_id", "=", user_id) for user_id in user_data
                    ),
                )
                for meeting_id, user_data in meeting_ids_to_user_ids_to_group_ids.items()
            ),
            [
                admin_group_id
                for meeting in meetings.values()
                if (admin_group_id := meeting.get("admin_group_id"))
            ],
            {
                group_id
                for user_data in meeting_ids_to_user_ids_to_group_ids.values()
                for group_list in user_data.values()
                for group_id in group_list
            },
        )
