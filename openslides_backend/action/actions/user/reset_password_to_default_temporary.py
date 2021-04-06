from ....permissions.permissions import Permissions
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryMixin
from .reset_password_to_default import UserResetPasswordToDefaultAction


@register_action("user.reset_password_to_default_temporary")
class UserResetPasswordToDefaultTemporaryAction(
    CheckTemporaryMixin, UserResetPasswordToDefaultAction
):
    """
    Action to reset a password to default of a temporary user.
    """

    permission = Permissions.User.CAN_MANAGE
