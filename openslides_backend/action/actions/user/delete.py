from typing import Any, Dict

from openslides_backend.permissions.management_levels import OrganisationManagementLevel
from openslides_backend.permissions.permission_helper import is_temporary
from openslides_backend.shared.exceptions import ActionException

from ....models.models import User
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryNoForInstanceMixin


@register_action("user.delete")
class UserDelete(CheckTemporaryNoForInstanceMixin, DeleteAction):
    """
    Action to delete a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_delete_schema()
    permission = OrganisationManagementLevel.CAN_MANAGE_USERS

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if is_temporary(self.datastore, instance):
            raise ActionException(
                f"User {instance['id']} is a temporary user. Use user.delete_temporary to delete him."
            )
        return instance
