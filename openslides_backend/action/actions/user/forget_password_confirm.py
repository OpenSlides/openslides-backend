from collections.abc import Callable
from typing import Any
from urllib.parse import unquote

from authlib.exceptions import InvalidCredentialsException

from openslides_backend.action.util.typing import ActionData

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .password_mixins import ClearSessionsMixin


@register_action("user.forget_password_confirm")
class UserForgetPasswordConfirm(UpdateAction, ClearSessionsMixin):
    """
    Action to set a forgotten password.
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        title="user forget password confirm schema",
        additional_required_fields={
            "new_password": {"type": "string"},
            "user_id": required_id_schema,
            "authorization_token": {"type": "string"},
        },
    )
    skip_archived_meeting_check = True

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        user_id = instance.pop("user_id")
        user = self.datastore.get(f"user/{user_id}", ["saml_id"], lock_result=False)
        new_password = instance.pop("new_password")
        if user.get("saml_id"):
            raise ActionException(
                f"user {user['saml_id']} is a Single Sign On user and has no local OpenSlides password."
            )
        token = instance.pop("authorization_token")
        self.check_token(user_id, token)
        instance["id"] = user_id
        instance["password"] = self.auth.hash(new_password)
        return instance

    def check_token(self, user_id: int, token: str) -> None:
        try:
            if not self.auth.verify_authorization_token(user_id, unquote(token)):
                raise ActionException("Failed to verify token.")
        except InvalidCredentialsException:
            raise ActionException("Failed to verify token.")

    def check_permissions(self, instance: dict[str, Any]) -> None:
        pass

    def get_on_success(self, action_data: ActionData) -> Callable[[], None] | None:
        def on_success() -> None:
            self.auth.clear_all_sessions()

        return on_success
