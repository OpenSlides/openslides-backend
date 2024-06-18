from collections.abc import Callable
from typing import Any

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ....shared.exceptions import ActionException
from ...action import Action
from ...util.typing import ActionData


class SetPasswordMixin(Action):
    def reset_password(self, instance: dict[str, Any]) -> None:
        instance["password"] = instance["default_password"]
        self.set_password(instance)

    def set_password(self, instance: dict[str, Any]) -> None:
        """
        Hashes the password given in the instance (which is assumed to be plain text) and sets it as
        the default password if `set_as_default` is True in the instance.
        """
        if "meta_new" not in instance:
            user = self.datastore.get(
                fqid_from_collection_and_id("user", instance["id"]),
                ["saml_id"],
                lock_result=False,
            )
        else:
            user = instance
        if user.get("saml_id"):
            raise ActionException(
                f"user {user['saml_id']} is a Single Sign On user and has no local OpenSlides password."
            )

        password = instance.pop("password")
        instance["password"] = self.auth.hash(password)
        if instance.pop("set_as_default", False):
            instance["default_password"] = password


class ClearSessionsMixin(Action):
    """Adds an on_success method to the action that clears all sessions."""

    def get_on_success(self, action_data: ActionData) -> Callable[[], None] | None:
        def on_success() -> None:
            self.auth.clear_all_sessions()

        # only clear session if the user changed his own password
        if any(instance["id"] == self.user_id for instance in action_data):
            return on_success
        else:
            return None
