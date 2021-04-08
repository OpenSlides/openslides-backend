from typing import Any, Dict

from ....models.models import User
from ....permissions.permissions import Permissions
from ....shared.schema import id_list_schema
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .temporary_user_mixin import TemporaryUserMixin
from .user_mixin import UserMixin


@register_action("user.create_temporary")
class UserCreateTemporary(CreateAction, TemporaryUserMixin, UserMixin):
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
            "is_physical_person",
            "default_password",
            "gender",
            "email",
            "default_number",
            "default_structure_level",
            "default_vote_weight",
            "is_present_in_meeting_ids",
        ],
        additional_optional_fields={
            "group_ids": id_list_schema,
            "vote_delegations_from_ids": id_list_schema,
            "comment": User().comment_.get_schema(),
            "number": User().number_.get_schema(),
            "structure_level": User().structure_level_.get_schema(),
            "about_me": User().about_me_.get_schema(),
            "vote_weight": User().vote_weight_.get_schema(),
        },
    )
    permission = Permissions.User.CAN_MANAGE

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = self.update_instance_temporary_user(instance)
        return super().base_update_instance(instance)
