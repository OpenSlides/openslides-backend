from typing import Any, Dict, cast

from ....permissions.management_levels import CommitteeManagementLevel
from ....permissions.permission_helper import has_committee_management_level
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.patterns import fqid_from_collection_and_id
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
        if not ("start_time" in instance or "end_time" in instance):
            return
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["id"]),
            ["start_time", "end_time"],
            raise_exception=False,
        )
        start_time = (
            instance["start_time"]
            if "start_time" in instance
            else meeting.get("start_time")
        )
        end_time = (
            instance["end_time"] if "end_time" in instance else meeting.get("end_time")
        )

        if start_time and not end_time or not start_time and end_time:
            raise ActionException("Only one of start_time and end_time is not allowed.")


class GetMeetingIdFromIdMixin(Action):
    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        return cast(int, instance.get("id"))
