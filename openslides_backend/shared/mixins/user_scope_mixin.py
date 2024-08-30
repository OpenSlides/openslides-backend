from collections import defaultdict
from enum import Enum
from typing import Any

from openslides_backend.shared.base_service_provider import BaseServiceProvider

from ...permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ...permissions.permission_helper import (
    get_shared_committee_management_levels,
    has_committee_management_level,
    has_organization_management_level,
    has_perm,
)
from ...permissions.permissions import Permission, Permissions
from ...services.datastore.interface import GetManyRequest
from ..exceptions import MissingPermission, PermissionDenied
from ..patterns import fqid_from_collection_and_id


class UserScope(str, Enum):
    Meeting = "meeting"
    Committee = "committee"
    Organization = "organization"

    def __repr__(self) -> str:
        return repr(self.value)


class UserScopeMixin(BaseServiceProvider):
    def get_user_scope(
        self, id_or_instance: int | dict[str, Any]
    ) -> tuple[UserScope, int, str, dict[int, Any]]:
        """
        Parameter id_or_instance: id for existing user or instance for user to create
        Returns the scope of the given user id together with the relevant scope id (either meeting,
        committee or organization), the OML level of the user as string (empty string if the user
        has none) and the ids of all committees that the user is either a manager in or a member of.
        and their respective meetings the user is part of. #A committe can have no meetings if the
        user just has committee management rights and is not part of any of its meetings.
        """
        meetings: set[int] = set()
        committees_manager: set[int] = set()
        if isinstance(id_or_instance, dict):
            if "group_ids" in id_or_instance:
                if "meeting_id" in id_or_instance:
                    meetings.add(id_or_instance["meeting_id"])
            committees_manager.update(
                set(id_or_instance.get("committee_management_ids", []))
            )
            oml_right = id_or_instance.get("organization_management_level", "")
        else:
            user = self.datastore.get(
                fqid_from_collection_and_id("user", id_or_instance),
                [
                    "meeting_ids",
                    "organization_management_level",
                    "committee_management_ids",
                ],
            )
            meetings.update(user.get("meeting_ids", []))
            committees_manager.update(set(user.get("committee_management_ids") or []))
            oml_right = user.get("organization_management_level", "")
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting",
                    list(meetings),
                    ["committee_id", "is_active_in_organization_id"],
                )
            ]
        ).get("meeting", {})

        meetings_committee: dict[int, int] = {
            meeting_id: meeting_data["committee_id"]
            for meeting_id, meeting_data in result.items()
            if meeting_data.get("is_active_in_organization_id")
        }
        committees = committees_manager | set(meetings_committee.values())
        committee_meetings: dict[int, Any] = defaultdict(list)
        for meeting, committee in meetings_committee.items():
            committee_meetings[committee].append(meeting)
        for committee in committees:
            if committee not in committee_meetings.keys():
                committee_meetings[committee] = None

        if len(meetings_committee) == 1 and len(committees) == 1:
            return (
                UserScope.Meeting,
                next(iter(meetings_committee)),
                oml_right,
                committee_meetings,
            )
        elif len(committees) == 1:
            return (
                UserScope.Committee,
                next(iter(committees)),
                oml_right,
                committee_meetings,
            )
        return UserScope.Organization, 1, oml_right, committee_meetings

    def check_permissions_for_scope(
        self,
        instance_id: int,
        always_check_user_oml: bool = True,
        meeting_permission: Permission = Permissions.User.CAN_MANAGE,
    ) -> None:
        """
        Checks the permissions for user-altering actions depending on the user scope.
        With check_user_oml_always=True it will be checked whether the request user
        has at minimum the same OML-level than the requested user to pass.
        Reason: A user with OML-level-permission has scope "meeting" or "committee" if
        he belongs to only 1 meeting or 1 committee.
        """
        scope, scope_id, user_oml, committees_to_meetings = self.get_user_scope(
            instance_id
        )
        if (
            always_check_user_oml
            and user_oml
            and not has_organization_management_level(
                self.datastore,
                self.user_id,
                perm := OrganizationManagementLevel(user_oml),
            )
        ):
            raise MissingPermission({perm: 1})
        if has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            return

        if scope == UserScope.Committee:
            if not has_committee_management_level(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                scope_id,
            ):
                raise MissingPermission(
                    {
                        OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                        CommitteeManagementLevel.CAN_MANAGE: scope_id,
                    }
                )
        elif scope == UserScope.Meeting:
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", scope_id),
                ["committee_id"],
                lock_result=False,
            )
            if not has_committee_management_level(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                meeting["committee_id"],
            ) and not has_perm(
                self.datastore, self.user_id, meeting_permission, scope_id
            ):
                raise MissingPermission(
                    {
                        OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                        CommitteeManagementLevel.CAN_MANAGE: meeting["committee_id"],
                        meeting_permission: scope_id,
                    }
                )
        else:
            if get_shared_committee_management_levels(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                [ci for ci in committees_to_meetings.keys()],
            ):
                return
            meeting_ids = set()
            for mi in committees_to_meetings.values():
                meeting_ids.add(*mi)
            if not self.check_for_admin_in_all_meetings(instance_id, meeting_ids):#
                raise MissingPermission(
                    {OrganizationManagementLevel.CAN_MANAGE_USERS: 1}
                )

    def check_for_admin_in_all_meetings(self, instance_id: int, b_meeting_ids: set[int] = None) -> bool:#
        """
        Checks if the requesting user has permissions to manage participants in all of requested users meetings.
        Also checks if the requesting user has meeting admin rights and the requested user doesn't.
        Returns true if permissions are given. False if not. Raises no Exceptions. TODO ooops!!!
        """
        if not instance_id:
            return False
        if not b_meeting_ids:
            b_meeting_ids = set()
            for mi in self.instance_committee_meeting_ids.values():
                b_meeting_ids.add(*mi)
        if not b_meeting_ids:
            return False
        if hasattr(self, "permstore"):
            a_meeting_ids = self.permstore.user_meetings
        else:
            a_user = self.datastore.get(
                fqid_from_collection_and_id("user", instance_id),
                ["meeting_ids"],
                lock_result=False,
            )
            a_meeting_ids = set(a_user.get("meeting_ids", []))
        if not a_meeting_ids:
            return False
        intersection_meeting_ids = a_meeting_ids.intersection(b_meeting_ids)
        if not b_meeting_ids.issubset(intersection_meeting_ids):
            return False
        intersection_meetings = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting",
                    list(intersection_meeting_ids),
                    ["admin_group_id", "group_ids", "meeting_user_ids"],
                )
            ],
            lock_result=False,
        ).get("meeting", {})
        for meeting_id, meeting_dict in intersection_meetings.items():
            # get meetings admins
            admin_meeting_users = {}
            # unnecessary "if" due to admin group always existant?
            if admin_group_id := meeting_dict.get("admin_group_id"):
                admin_group = self.datastore.get(
                    fqid_from_collection_and_id("group", admin_group_id),
                    ["meeting_user_ids"],
                    lock_result=False,
                )
                admin_meeting_users = self.datastore.get_many(
                    [
                        GetManyRequest(
                            "meeting_user",
                            admin_group.get("meeting_user_ids", []),
                            ["user_id"],
                        )
                    ],
                    lock_result=False,
                ).get("meeting_user", {})
            # unnecessary "if" due to default group always existant?
            if group_ids := meeting_dict.get("group_ids", []):
                groups = self.datastore.get_many(
                    [GetManyRequest("group", group_ids, ["meeting_user_ids"])],
                    lock_result=False,
                ).get("group", {})
                for group_id, group in groups.items():
                    meeting_user_ids = group.get("meeting_user_ids", [])
                    group_permissions = group.get("permissions", [])
                    if meeting_user_ids and (
                        "user.can_manage" in group_permissions
                        or "user.can_update" in group_permissions
                    ):  # TODO test mit can manage hier nur can update
                        admin_meeting_users.update(
                            self.datastore.get_many(
                                [
                                    GetManyRequest(
                                        "meeting_user",
                                        meeting_user_ids,
                                        ["user_id"],
                                    )
                                ],
                                lock_result=False,
                            ).get("meeting_user", {})
                        )
            else:
                return False
            # if instance/requested user is a meeting admin in this meeting.
            if admin_meeting_users:
                if [
                    admin_meeting_user
                    for admin_meeting_user in admin_meeting_users.values()
                    if admin_meeting_user.get("user_id") == instance_id
                ] != []:
                    return False
                # if requesting user is not a meeting admin in this meeting.
                if not next(
                    iter(
                        admin_meeting_user
                        for admin_meeting_user in admin_meeting_users.values()
                        if admin_meeting_user.get("user_id") == self.user_id
                    )
                ):
                    return False
            else:
                return False
        return True
