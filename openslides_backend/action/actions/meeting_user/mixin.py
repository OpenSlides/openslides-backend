from typing import Any, Dict, Tuple, cast

from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from openslides_backend.permissions.permissions import Permissions

from ....shared.exceptions import MissingPermission, PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id
from .history_mixin import MeetingUserHistoryMixin


class MeetingUserMixin(MeetingUserHistoryMixin):
    standard_fields = [
        "comment",
        "number",
        "structure_level",
        "vote_weight",
        "personal_note_ids",
    ]

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        """standard_fields have to be checked for user.can_manage, which is always sufficient and
        even needed, if there is no data at all exempt the required fields.
        Special fields like about_me and group_ids could be managed also with other permissions.
        Details see https://github.com/OpenSlides/OpenSlides/wiki/meeting_user.create"""
        if any(field in self.standard_fields for field in instance.keys()) or not any(
            field in ["about_me", "group_ids"] for field in instance
        ):
            return super().check_permissions(instance)

        def get_user_and_meeting_id() -> Tuple[int, int]:
            fields = ["user_id", "meeting_id"]
            if any(field not in instance for field in fields):
                mu = self.datastore.get(
                    fqid_from_collection_and_id("meeting_user", instance["id"]),
                    ["user_id", "meeting_id"],
                    lock_result=False,
                )
            else:
                mu = instance
            return cast(Tuple[int, int], tuple(mu[field] for field in fields))

        def get_request_user_data() -> Dict[str, Any]:
            return self.datastore.get(
                fqid_from_collection_and_id("user", self.user_id),
                ["organization_management_level", "committee_management_ids"],
                lock_result=False,
            )

        def get_committee_id() -> int:
            return self.datastore.get(
                fqid_from_collection_and_id("meeting", meeting_id),
                ["committee_id"],
                lock_result=False,
            )["committee_id"]

        def raise_own_exception() -> bool:
            try:
                super(MeetingUserMixin, self).check_permissions(instance)
                return False
            except PermissionDenied:
                return True

        user_id, meeting_id = get_user_and_meeting_id()
        if "about_me" in instance:
            if self.user_id != user_id:
                if raise_own_exception():
                    raise PermissionDenied(
                        f"The user needs Permission user.can_manage in meeting {meeting_id} to set 'about me', if it is not his own"
                    )
                else:
                    return

        if "group_ids" in instance:
            user = get_request_user_data()
            if (
                OrganizationManagementLevel(user.get("organization_management_level"))
                < OrganizationManagementLevel.CAN_MANAGE_USERS
            ):
                committee_id = get_committee_id()
                if (
                    committee_id not in user.get("committee_management_ids", [])
                    and raise_own_exception()
                ):
                    raise MissingPermission(
                        {
                            OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                            CommitteeManagementLevel.CAN_MANAGE: committee_id,
                            Permissions.User.CAN_MANAGE: meeting_id,
                        }
                    )
