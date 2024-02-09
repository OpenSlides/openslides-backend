from typing import Any

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.mixins.user_scope_mixin import UserScopeMixin
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user.delete")
class UserDelete(UserScopeMixin, DeleteAction):
    """
    Action to delete a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_delete_schema()
    skip_archived_meeting_check = True
    history_information = "Account deleted"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        if instance["id"] == self.user_id:
            raise ActionException("You cannot delete yourself.")
        return super().update_instance(instance)

    def check_permissions(self, instance: dict[str, Any]) -> None:
        self.check_permissions_for_scope(instance["id"])

    def get_removed_meeting_id(self, instance: dict[str, Any]) -> int | None:
        return 0
