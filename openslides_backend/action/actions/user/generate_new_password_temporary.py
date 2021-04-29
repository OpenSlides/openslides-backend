from ....models.models import User
from ....permissions.permissions import Permissions
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryYesForInstanceMixin
from .generate_new_password import UserGenerateNewPasswordMixin


@register_action("user.generate_new_password_temporary")
class UserGenerateNewPasswordTemporaryAction(
    CheckTemporaryYesForInstanceMixin, UserGenerateNewPasswordMixin
):
    model = User()
    schema = DefaultSchema(User()).get_update_schema()
    permission = Permissions.User.CAN_MANAGE
