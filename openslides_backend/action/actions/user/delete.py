from typing import Any, Dict

from ....models.models import User
from ....shared.exceptions import ActionException
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .user_scope_permission_check_mixin import UserScopePermissionCheckMixin


@register_action("user.delete")
class UserDelete(UserScopePermissionCheckMixin, DeleteAction):
    """
    Action to delete a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_delete_schema()
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if instance["id"] == self.user_id:
            raise ActionException("You cannot delete yourself.")
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        self.check_permissions_for_scope(instance, check_user_oml_always=True)
