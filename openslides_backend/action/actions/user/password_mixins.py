from typing import Any, Callable, Dict

from ....shared.exceptions import ActionException
from ...action import Action
from ...generics.update import UpdateAction
from ...util.typing import ActionData


class UserSetPasswordMixin(UpdateAction):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        set hashed password and set default password if set_as_default is True.
        """
        user = self.datastore.get(
            f"user/{instance['id']}", ["saml_id"], lock_result=False
        )
        if user.get("saml_id"):
            raise ActionException(
                f"user {user['saml_id']} is a Single Sign On user and has no local Openslides passwort."
            )

        password = instance.pop("password")
        set_as_default = False
        if "set_as_default" in instance:
            set_as_default = instance.pop("set_as_default")
        hashed_password = self.auth.hash(password)
        instance["password"] = hashed_password
        if set_as_default:
            instance["default_password"] = password
        return instance


class PasswordMixin(Action):
    def set_password(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        password = instance["default_password"]
        hashed_password = self.auth.hash(password)
        instance["password"] = hashed_password
        return instance


class PasswordChangeMixin(Action):
    """Adds an on_success method to the action that clears all sessions."""

    def get_on_success(self, action_data: ActionData) -> Callable[[], None] | None:
        def on_success() -> None:
            self.auth.clear_all_sessions()

        if self.user_id > 0:
            return on_success
        else:
            return None
