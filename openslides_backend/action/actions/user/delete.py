from ....models.models import User
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user.delete")
class UserDelete(DeleteAction):
    """
    Action to delete a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_delete_schema()
