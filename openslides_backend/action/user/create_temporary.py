from typing import Any, Dict

from ...models.models import User
from ...shared.schema import id_list_schema
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action
from .temporary_user_mixin import TemporaryUserMixin


@register_action("user.create_temporary")
class UserCreateTemporary(CreateAction, TemporaryUserMixin):
    """
    Action to create a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_create_schema(
        required_properties=["meeting_id", "username"],
        optional_properties=[
            "title",
            "first_name",
            "last_name",
            "is_active",
            "is_committee",
            "about_me",
            "gender",
            "comment",
            "number",
            "structure_level",
            "email",
            "vote_weight",
            "is_present_in_meeting_ids",
            "default_password",
        ],
        additional_optional_fields={"group_ids": id_list_schema},
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        return self.update_instance_temporary_user(instance)
