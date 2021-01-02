from typing import Any, Dict

from ....models.models import User
from ....shared.exceptions import ActionException
from ...action import PERMISSION_SPECIAL_CASE
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user.update_self")
class UserUpdate(UpdateAction):
    """
    Action to self update a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        optional_properties=["username", "about_me", "email"]
    )
    permission_description = PERMISSION_SPECIAL_CASE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set id = user_id.
        """
        if self.auth.is_anonymous(self.user_id):
            raise ActionException("Can't update for anonymous")
        instance["id"] = self.user_id
        return instance
