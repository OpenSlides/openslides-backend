from ..base import DummyAction
from ..register import register_action
from . import (  # noqa
    create,
    create_temporary,
    delete,
    delete_temporary,
    generate_new_password,
    reset_password_to_default,
    reset_password_to_default_temporary,
    set_password,
    set_password_self,
    update,
    update_self,
    update_temporary,
)


@register_action("user.reset_password")
class UserResetPassword(DummyAction):
    pass


@register_action("user.set_password_temporary")
class UserSetPasswordTemporary(DummyAction):
    pass
