from typing import Any, Dict

from ....models.models import User
from ....shared.schema import id_list_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryMixin
from .temporary_user_mixin import TemporaryUserMixin


@register_action("user.update_temporary")
class UserUpdateTemporary(UpdateAction, TemporaryUserMixin, CheckTemporaryMixin):
    """
    Action to update a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        optional_properties=[
            "username",
            "title",
            "first_name",
            "last_name",
            "is_active",
            "is_physical_person",
            "default_password",
            "gender",
            "email",
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

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        self.check_for_temporary(instance)
        instance = self.update_instance_temporary_user(instance)
        # remove meeting_id again to not write it to db
        del instance["meeting_id"]
        return super().base_update_instance(instance)
