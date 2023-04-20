from typing import Any, Dict, cast

from ....permissions.management_levels import CommitteeManagementLevel
from ....permissions.permission_helper import has_committee_management_level
from ....shared.exceptions import ActionException, MissingPermission
from ...action import Action


class MeetingPermissionMixin(Action):
    def check_permissions(self, instance: Dict[str, Any]) -> None:
        is_manager = has_committee_management_level(
            self.datastore,
            self.user_id,
            CommitteeManagementLevel.CAN_MANAGE,
            self.get_committee_id(instance),
        )
        if not is_manager:
            raise MissingPermission(CommitteeManagementLevel.CAN_MANAGE)

    def get_committee_id(self, instance: Dict[str, Any]) -> int:
        return instance["committee_id"]


class MeetingCheckTimesMixin(Action):
    def check_start_and_end_time(self, instance: Dict[str, Any]) -> None:
        if (
            instance.get("start_time")
            and not instance.get("end_time")
            or not instance.get("start_time")
            and instance.get("end_time")
        ):
            raise ActionException("Only one of start_time and end_time is not allowed.")


class GetMeetingIdFromIdMixin(Action):
    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        return cast(int, instance.get("id"))
