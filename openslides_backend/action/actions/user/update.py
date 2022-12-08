from typing import Any, Dict

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import PermissionException
from ....shared.patterns import ID_REGEX, fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .set_present import UserSetPresentAction
from .user_mixin import LimitOfUserMixin, UpdateHistoryMixin, UserMixin


@register_action("user.update")
class UserUpdate(
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
        additional_optional_fields={
            "presence": {
                "type": "object",
                "additionalProperties": False,
                "patternProperties": {ID_REGEX: "boolean"},
            }
        },
    )

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

        presence = instance.pop("presence", None)
        if presence:
            action_payload = [
                {
                    "id": instance["id"],
                    "meeting_id": int(meeting_id),
                    "present": present,
                }
                for meeting_id, present in presence.items()
            ]
            self.execute_other_action(UserSetPresentAction, action_payload)
        return instance
