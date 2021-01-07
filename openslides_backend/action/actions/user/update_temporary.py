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
        additional_optional_fields={
            "group_ids": id_list_schema,
            "vote_delegations_from_ids": id_list_schema,
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        self.check_for_temporary(instance)
        instance = self.update_instance_temporary_user(instance)
        # remove meeting_id again to not write it to db
        del instance["meeting_id"]
        return instance
