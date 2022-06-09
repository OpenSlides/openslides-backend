from typing import Any, Dict

from ....models.models import User
from ....shared.exceptions import PermissionException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .user_mixin import LimitOfUserMixin, UserMixin
from ....permissions.management_levels import (
    OrganizationManagementLevel,
)

@register_action("user.update")
class UserUpdate(
    UserMixin,
    CreateUpdatePermissionsMixin,
    UpdateAction,
    LimitOfUserMixin,
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
            "committee_$_management_level",
            "number_$",
            "structure_level_$",
            "vote_weight_$",
            "about_me_$",
            "comment_$",
            "vote_delegated_$_to_id",
            "vote_delegations_$_from_ids",
            "group_$_ids",
            "is_demo_user",
        ],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        user = self.datastore.get(
            fqid_from_collection_and_id("user", instance["id"]),
            mapped_fields=[
                "is_active",
                "organization_management_level",
            ],
        )
        if instance["id"] == self.user_id and user["organization_management_level"] == OrganizationManagementLevel.SUPERADMIN:
            if "organization_management_level" in instance and instance.get("organization_management_level") != OrganizationManagementLevel.SUPERADMIN:
                raise PermissionException("A user is not allowed to withdraw his own 'superadmin'-Organization-Management-Level.")
            if "is_active" in instance and instance.get("is_active") is not True:
                raise PermissionException("A superadmin is not allowed to set himself inactive.")
        if instance.get("is_active") and not user.get("is_active"):
            self.check_limit_of_user(1)
        return super().update_instance(instance)
