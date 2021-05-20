from typing import Any, Dict

from ....permissions.management_levels import CommitteeManagementLevel
from ....permissions.permission_helper import has_committee_management_level
from ....shared.exceptions import MissingPermission
from ...action import Action


class MeetingPermissionMixin(Action):
    def check_permissions(self, instance: Dict[str, Any]) -> None:
        is_manager = has_committee_management_level(
            self.datastore,
            self.user_id,
            self.get_committee_id(instance),
            CommitteeManagementLevel.CAN_MANAGE,
        )
        if not is_manager:
            raise MissingPermission(CommitteeManagementLevel.CAN_MANAGE)

    def get_committee_id(self, instance: Dict[str, Any]) -> int:
        return instance["committee_id"]
