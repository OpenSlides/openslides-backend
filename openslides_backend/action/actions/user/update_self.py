from typing import Any, Dict

from ....models.models import User
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .user_mixin import UserMixin


@register_action("user.update_self")
class UserUpdateSelf(UpdateAction, UserMixin):
    """
    Action to self update a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        optional_properties=["username", "pronoun", "gender", "email"]
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set id = user_id.
        """
        instance["id"] = self.user_id
        instance = super().update_instance(instance)
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        self.assert_not_anonymous()
