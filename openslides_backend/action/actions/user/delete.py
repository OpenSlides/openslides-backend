from typing import Any, Dict

from openslides_backend.permissions.permission_helper import (
    has_organisation_management_level,
    is_temporary,
)
from openslides_backend.permissions.permissions import OrganisationManagementLevel
from openslides_backend.shared.exceptions import ActionException, PermissionDenied

from ....models.models import User
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user.delete")
class UserDelete(DeleteAction):
    """
    Action to delete a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_delete_schema()

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if has_organisation_management_level(
            self.datastore, self.user_id, OrganisationManagementLevel.CAN_MANAGE_USERS
        ):
            return

        msg = f"You are not allowed to perform action {self.name}. Missing Organisation Management Level: {OrganisationManagementLevel.CAN_MANAGE_USERS}"
        raise PermissionDenied(msg)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if is_temporary(self.datastore, instance):
            raise ActionException(
                f"User {instance['id']} is a temporary user. Use user.delete_temporary to delete him."
            )
        return instance
