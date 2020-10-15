from ...models.models import User
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("user.update_self")
class UserUpdate(UpdateAction):
    """
    Action to self update a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        optional_properties=["username", "about_me", "email"]
    )
