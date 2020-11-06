from ..base import DummyAction
from ..register import register_action
from . import (  # noqa
    create,
    create_temporary,
    delete,
    delete_temporary,
    reset_password_to_default,
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


@register_action("user.reset_passsword_to_default_temporary")
class UserSetPasswordToDefaultTemporary(DummyAction):
    pass
