from typing import Any, Dict, List

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import ActionException, PermissionException
from ....shared.functions.count_users_for_limit import get_user_counting_to_add_function
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import optional_id_schema
from ...action import original_instances
from ...generics.update import UpdateAction
from ...mixins.send_email_mixin import EmailCheckMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .user_mixin import (
    LimitOfUserMixin,
    UpdateHistoryMixin,
    UserMixin,
    check_gender_helper,
)


@register_action("user.update")
class UserUpdate(
    EmailCheckMixin,
    UserMixin,
    CreateUpdatePermissionsMixin,
    UpdateAction,
    LimitOfUserMixin,
    UpdateHistoryMixin,
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
            "gender",
            "email",
            "default_number",
            "default_structure_level",
            "default_vote_weight",
            "organization_management_level",
            "committee_management_ids",
            "is_demo_user",
            "saml_id",
        ],
        additional_optional_fields={
            "meeting_id": optional_id_schema,
            **UserMixin.transfer_field_list,
        },
    )
    check_email_field = "email"

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        """
        The check for limit of users has to be implemented here for all changed users
        """
        old: List[int] = []
        new: List[tuple[bool, List[int]]] = []
        for instance in action_data:
            old.append(instance.get("id"))
            new.append((instance.get("is_active"), instance.get("group_ids")))
        user_counting_to_add_function = get_user_counting_to_add_function(old, new)
        self.check_limit_of_user(user_counting_to_add_function)
        return action_data

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        user = self.datastore.get(
            fqid_from_collection_and_id("user", instance["id"]),
            mapped_fields=[
                "is_active",
                "organization_management_level",
                "saml_id",
            ],
        )
        if user.get("saml_id") and (
            instance.get("can_change_own_password") or instance.get("default_password")
        ):
            raise ActionException(
                f"user {user['saml_id']} is a Single Sign On user and may not set the local default_passwort or the right to change it locally."
            )

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

        check_gender_helper(self.datastore, instance)
        return instance
