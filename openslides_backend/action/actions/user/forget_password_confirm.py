from typing import Any, Dict

from ....models.models import User
from ....shared.exceptions import ActionException
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
            "user_id": {"type": "integer"},
            "token": {"type": "string"},
        },
    )
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        user_id = instance.pop("user_id")
        new_password = instance.pop("new_password")
        token = self.get_token(instance)
        self.check_token(user_id, token)
        instance["id"] = user_id
        instance["password"] = self.auth.hash(new_password)
        return instance

    def get_token(self, instance: Dict[str, Any]) -> str:
        # TODO Perhaps get the token from the header.
        return instance.pop("token")

    def check_token(self, user_id: int, token: str) -> None:
        if not self.auth.verify_authorization_token(user_id, "bearer " + token):
            raise ActionException("Failed to verify token.")

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
