from ....models.models import User
from ....permissions.permissions import Permissions
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryYesForInstanceMixin
from .set_password import UserSetPasswordMixin


@register_action("user.set_password_temporary")
class UserSetPasswordTemporaryAction(
    CheckTemporaryYesForInstanceMixin, UserSetPasswordMixin
):
    """
    Action to set the password of a temporary user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        required_properties=["password"],
        additional_optional_fields={"set_as_default": {"type": "boolean"}},
    )
    permission = Permissions.User.CAN_MANAGE
