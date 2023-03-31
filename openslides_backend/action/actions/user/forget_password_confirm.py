from typing import Any, Dict
from urllib.parse import unquote

from authlib.exceptions import InvalidCredentialsException

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user.forget_password_confirm")
class UserForgetPasswordConfirm(UpdateAction):
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        user_id = instance.pop("user_id")
        new_password = instance.pop("new_password")
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

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
