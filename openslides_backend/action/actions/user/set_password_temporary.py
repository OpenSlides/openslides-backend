from ....permissions.permissions import Permissions
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryMixin
from .set_password import UserSetPasswordAction


@register_action("user.set_password_temporary")
class UserSetPasswordTemporaryAction(CheckTemporaryMixin, UserSetPasswordAction):
    """
    Action to set the password of a temporary user.
    """

    permission = Permissions.User.CAN_MANAGE
