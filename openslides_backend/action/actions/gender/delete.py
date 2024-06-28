from typing import Any

from ....models.models import Gender
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import GenderPermissionMixin


@register_action("gender.delete")
class GenderDeleteAction(DeleteAction, GenderPermissionMixin):
    """
    Action to delete a gender.
    """

    model = Gender()
    schema = DefaultSchema(Gender()).get_delete_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS
    skip_archived_meeting_check = True

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        super().check_editable(instance)
        return instance
