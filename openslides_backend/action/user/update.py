from ...models.models import User
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("user.update")
class UserUpdate(UpdateAction):
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
            "is_committee",
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
        ]
    )
