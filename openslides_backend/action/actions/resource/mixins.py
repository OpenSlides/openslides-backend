from typing import Any, Dict

from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....shared.exceptions import MissingPermission
from ...action import Action


class PermissionMixin(Action):
    def check_permissions(self, instance: Dict[str, Any]) -> None:
        self.assert_not_anonymous()
        if not has_organization_management_level(
            self.datastore,
            self.user_id,
            OrganizationManagementLevel.CAN_MANAGE_ORGANISATION,
        ):
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_ORGANISATION)
