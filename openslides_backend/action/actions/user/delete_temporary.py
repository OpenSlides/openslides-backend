from ....models.models import User
from ....permissions.permissions import Permissions
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryYesForInstanceMixin


@register_action("user.delete_temporary")
class UserDeleteTemporary(CheckTemporaryYesForInstanceMixin, DeleteAction):
    """
    Action to delete a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_delete_schema()
    permission = Permissions.User.CAN_MANAGE
