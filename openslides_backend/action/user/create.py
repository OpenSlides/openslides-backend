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
        required_properties=["username"],
        optional_properties=[
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
            "vote_weight",
            "role_id",
            "is_present_in_meeting_ids",
            "guest_meeting_ids",
            "committee_as_member_ids",
            "committee_as_manager_ids",
        ],
    )
