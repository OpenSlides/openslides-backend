from ...models.models import User
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action


@register_action("user.create_temporary")
class UserCreateTemporary(CreateAction):
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
            # "vote_weight",
            "is_present_in_meeting_ids",
        ],
    )
