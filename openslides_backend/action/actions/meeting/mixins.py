from typing import Any, Dict, Optional, cast

from ....permissions.management_levels import CommitteeManagementLevel
from ....permissions.permission_helper import has_committee_management_level
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.patterns import fqid_from_collection_and_id
from ...action import Action
from ...mixins.check_unique_name_mixin import CheckUniqueInContextMixin


class MeetingPermissionMixin(CheckUniqueInContextMixin):
    def validate_instance(self, instance: Dict[str, Any]) -> None:
        super().validate_instance(instance)
        if instance.get("external_id"):
            self.check_unique_in_context(
                "external_id",
                instance["external_id"],
                "The external_id of the meeting is not unique in the committee scope.",
                None,
                "committee_id",
                self.get_committee_id(instance),
            )

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        committee_id = self.get_committee_id(instance)
        if not has_committee_management_level(
            self.datastore,
            self.user_id,
            CommitteeManagementLevel.CAN_MANAGE,
            committee_id,
        ):
            raise MissingPermission({CommitteeManagementLevel.CAN_MANAGE: committee_id})

    def get_committee_id(self, instance: Dict[str, Any]) -> int:
        return instance["committee_id"]


class MeetingCheckTimesMixin(Action):
    def check_start_and_end_time(
        self, instance: Dict[str, Any], db_instance: Optional[Dict[str, Any]] = None
    ) -> None:
        if not ("start_time" in instance or "end_time" in instance):
            return
        if db_instance is None:
            db_instance = self.datastore.get(
                fqid_from_collection_and_id("meeting", instance["id"]),
                ["start_time", "end_time"],
                raise_exception=False,
            )
        start_time = instance.get("start_time", db_instance.get("start_time"))
        end_time = instance.get("end_time", db_instance.get("end_time"))
        if start_time and not end_time or not start_time and end_time:
            raise ActionException("Only one of start_time and end_time is not allowed.")
        if start_time and end_time and start_time > end_time:
            raise ActionException("start_time must be before end_time.")


class GetMeetingIdFromIdMixin(Action):
    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        return cast(int, instance.get("id"))
