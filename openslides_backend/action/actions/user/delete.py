from typing import Any, Dict

from ....models.models import User
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

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        self.check_permissions_for_scope(instance)
