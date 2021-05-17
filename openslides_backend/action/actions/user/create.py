from typing import Any, Dict

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import Collection
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
        optional_properties=[
            "title",
            "username",
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
            "committee_ids",
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
        if not (
            instance.get("username")
            or instance.get("first_name")
            or instance.get("last_name")
        ):
            raise ActionException("Need username or first_name or last_name")
        if not instance.get("username"):
            instance["username"] = self.generate_username(instance)
        if not instance.get("default_password"):
            instance = self.generate_and_set_password(instance)
        else:
            instance = self.set_password(instance)
        return super().update_instance(instance)

    def generate_username(self, instance: Dict[str, Any]) -> str:
        count = 0

        while True:
            possible_space = (
                " " if instance.get("first_name") and instance.get("last_name") else ""
            )
            new_username = (
                instance.get("first_name", "")
                + possible_space
                + instance.get("last_name", "")
            )
            if count > 0:
                new_username += f" {count}"

            result = self.datastore.filter(
                Collection("user"),
                FilterOperator("username", "=", new_username),
                ["id"],
            )
            if result:
                count += 1
            else:
                break
        return new_username
