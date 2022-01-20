from typing import Any, Dict

from ....models.models import User
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .user_mixin import LimitOfUserMixin, UserMixin


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
            FullQualifiedId(Collection("user"), instance["id"]),
            mapped_fields=[
                "is_active",
            ],
        )

        if instance.get("is_active") and not user.get("is_active"):
            self.check_limit_of_user(1)
        return super().update_instance(instance)
