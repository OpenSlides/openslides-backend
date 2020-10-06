from ..base import DummyAction
from ..register import register_action


@register_action("user.create")
class UserCreate(DummyAction):
    pass


@register_action("user.update")
class UserUpdate(DummyAction):
    pass


@register_action("user.delete")
class UserDelete(DummyAction):
    pass


@register_action("user.reset_password")
class UserResetPassword(DummyAction):
    pass


@register_action("user.set_password")
class UserSetPassword(DummyAction):
    pass
