from typing import Any, Dict

from ....models.models import User
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .password_mixin import PasswordCreateMixin
from .user_mixin import UserMixin


@register_action("user.create")
class UserCreate(
    CreateAction, UserMixin, CreateUpdatePermissionsMixin, PasswordCreateMixin
):
    """
    Action to create a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_create_schema(
        required_properties=["username"],
        optional_properties=[
            "title",
            "first_name",
            "last_name",
            "is_active",
            "is_physical_person",
            "default_password",
            "gender",
            "email",
            "default_number",
            "default_structure_level",
            "default_vote_weight",
            "organisation_management_level",
            "is_present_in_meeting_ids",
            "guest_meeting_ids",
            "committee_as_member_ids",
            "committee_as_manager_ids",
            "group_$_ids",
            "vote_delegations_$_from_ids",
            "vote_delegated_$_to_id",
            "comment_$",
            "number_$",
            "structure_level_$",
            "about_me_$",
            "vote_weight_$",
        ],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if not instance.get("default_password"):
            instance = self.generate_and_set_password(instance)
        else:
            instance = self.set_password(instance)
        return super().update_instance(instance)
