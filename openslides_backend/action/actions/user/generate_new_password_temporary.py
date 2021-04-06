from ....permissions.permissions import Permissions
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryMixin
from .generate_new_password import UserGenerateNewPassword


@register_action("user.generate_new_password_temporary")
class UserGenerateNewPasswordTemporaryAction(
    CheckTemporaryMixin, UserGenerateNewPassword
):

    permission = Permissions.User.CAN_MANAGE
