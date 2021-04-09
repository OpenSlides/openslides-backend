from typing import Any, Dict

from ....models.models import User
from ....permissions.permissions import OrganisationManagementLevel
from ....shared.exceptions import ActionException
from ....shared.schema import id_list_schema, optional_id_schema
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user.merge_to_non_temporary")
class UserMergeToNonTemporaray(CreateAction):
    """
    Action to merge temporary users to one standard user.
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        required_properties=[
            "username",
        ],
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
        ],
        additional_required_fields={
            "user_ids": {
                "description": "A list of temporary user ids to merge into a standard user.",
                **id_list_schema,
            }
        },
        additional_optional_fields={
            "password_from_user_id": {
                "description": "The password hash from this user is copied. The user id must be given in user_ids! If it is empty, the default password is used.",
                **optional_id_schema,
            }
        },
    )
    permission = permission = OrganisationManagementLevel.CAN_MANAGE_USERS

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        raise ActionException(
            "This action is still not implemented, but permission checked"
        )
        return instance
