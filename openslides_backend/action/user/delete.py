from ...models.models import User
from ..default_schema import DefaultSchema
from ..generics import DeleteAction
from ..register import register_action


@register_action("user.delete")
class UserDelete(DeleteAction):
    """
    Action to delete a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_delete_schema()
