from typing import Any, Dict

from ....models.models import User
from ....shared.exceptions import ActionException
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .user_mixin import UserMixin


@register_action("user.update_self")
class UserUpdate(UpdateAction, UserMixin):
    """
    Action to self update a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        optional_properties=["username", "email"]
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set id = user_id.
        """
        instance = super().update_instance(instance)
        if self.auth.is_anonymous(self.user_id):
            raise ActionException("Can't update for anonymous")
        instance["id"] = self.user_id
        return instance
