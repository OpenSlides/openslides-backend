from ...models.models import User
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action


@register_action("user.create")
class UserCreate(CreateAction):
    """
    Action to create a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_create_schema(
        properties=[
            "username",
            "title",
            "first_name",
            "last_name",
            "is_active",
            "is_committee",
            "default_password",
            "about_me",
            "gender",
            "comment",
            "number",
            "structure_level",
            "email",
            # "vote_weight",
            "role_id",
            "is_present_in_meeting_ids",
        ],
        required_properties=["username"],
    )
