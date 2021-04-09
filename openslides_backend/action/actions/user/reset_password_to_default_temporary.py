from ....models.models import User
from ....permissions.permissions import Permissions
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryYesForInstanceMixin
from .reset_password_to_default import UserResetPasswordToDefaultMixin


@register_action("user.reset_password_to_default_temporary")
class UserResetPasswordToDefaultTemporaryAction(
    CheckTemporaryYesForInstanceMixin, UserResetPasswordToDefaultMixin
):
    """
    Action to reset a password to default of a temporary user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema()
    permission = Permissions.User.CAN_MANAGE
