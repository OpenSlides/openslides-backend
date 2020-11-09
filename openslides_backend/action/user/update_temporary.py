from typing import Any, Dict

from ...models.models import User
from ...shared.exceptions import ActionException
from ...shared.patterns import FullQualifiedId
from ...shared.schema import id_list_schema
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action
from .temporary_user_mixin import TemporaryUserMixin


@register_action("user.update_temporary")
class UserUpdateTemporary(UpdateAction, TemporaryUserMixin):
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
        additional_optional_fields={"group_ids": id_list_schema},
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        db_instance = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]), ["meeting_id"]
        )
        if not db_instance.get("meeting_id"):
            raise ActionException(f"User {instance['id']} is not temporary.")
        instance["meeting_id"] = db_instance["meeting_id"]
        instance = self.update_instance_temporary_user(instance)
        # remove meeting_id again to not write it to db
        del instance["meeting_id"]
        return instance
