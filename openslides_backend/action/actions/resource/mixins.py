from typing import Any, Dict

from ....permissions.management_levels import OrganisationManagementLevel
from ....permissions.permission_helper import has_organisation_management_level
from ....shared.exceptions import MissingPermission
from ...action import Action


class PermissionMixin(Action):
    def check_permissions(self, instance: Dict[str, Any]) -> None:
        self.assert_not_anonymous()
        if not has_organisation_management_level(
            self.datastore,
            self.user_id,
            OrganisationManagementLevel.CAN_MANAGE_ORGANISATION,
        ):
            raise MissingPermission(OrganisationManagementLevel.CAN_MANAGE_ORGANISATION)
