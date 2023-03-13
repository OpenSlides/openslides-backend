from typing import Any, Dict, Optional

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import PermissionException
from ....shared.patterns import FullQualifiedId, fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...mixins.send_email_mixin import EmailCheckMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .user_mixin import LimitOfUserMixin, UpdateHistoryMixin, UserMixin


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
    check_email_field = "email"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        user = self.datastore.get(
            fqid_from_collection_and_id("user", instance["id"]),
            mapped_fields=[
                "is_active",
                "organization_management_level",
            ],
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
        if instance.get("is_active") and not user.get("is_active"):
            self.check_limit_of_user(1)

        return instance

    def apply_instance(
        self, instance: Dict[str, Any], fqid: Optional[FullQualifiedId] = None
    ) -> None:
        if not fqid:
            fqid = fqid_from_collection_and_id(self.model.collection, instance["id"])
        if (
            fqid in self.datastore.changed_models
            and (cm_user := self.datastore.changed_models[fqid]).get("meta_new")
            and "group_$_ids" in instance
        ):
            instance["group_$_ids"].update(
                {k: cm_user.get(f"group_${k}_ids", []) for k in cm_user["group_$_ids"]}
            )
        self.datastore.apply_changed_model(fqid, instance)
