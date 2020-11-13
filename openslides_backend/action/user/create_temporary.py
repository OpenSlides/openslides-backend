from typing import Any, Dict

from ...models.models import User
from ...services.datastore.commands import GetManyRequest
from ...shared.exceptions import ActionException
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
        if "vote_delegations_from_ids" in instance:
            vote_delegations_from_ids = instance.pop("vote_delegations_from_ids")
            get_many_request = GetManyRequest(
                self.model.collection, vote_delegations_from_ids, ["id"]
            )
            gm_result = self.datastore.get_many([get_many_request])
            users = gm_result.get(self.model.collection, {})

            set_payload = set(vote_delegations_from_ids)
            diff = set_payload.difference(users.keys())
            if len(diff):
                raise ActionException(f"The following users were not found: {diff}")

            instance[
                f"vote_delegations_${instance['meeting_id']}_from_ids"
            ] = vote_delegations_from_ids
        return self.update_instance_temporary_user(instance)
