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
from ..exceptions import MissingPermission
from ..patterns import fqid_from_collection_and_id


class UserScope(str, Enum):
    Meeting = "meeting"
    Committee = "committee"
    Organization = "organization"

    def __repr__(self) -> str:
        return repr(self.value)


class UserScopeMixin(BaseServiceProvider):
    instance_committee_meeting_ids: dict
    name: str

    def get_user_scope(
        self, id_or_instance: int | dict[str, Any]
    ) -> tuple[UserScope, int, str, dict[int, Any]]:
        """
        Parameter id_or_instance: id for existing user or instance for user to create
        Returns the scope of the given user id together with the relevant scope id (either meeting,
        committee or organization), the OML level of the user as string (empty string if the user
        has none) and the ids of all committees that the user is either a manager in or a member of
        together with their respective meetings the user being part of. A committee can have no meetings if the
        user just has committee management rights and is not part of any of its meetings.
        """
        meeting_ids: set[int] = set()
        committees_manager: set[int] = set()
        if isinstance(id_or_instance, dict):
            if "group_ids" in id_or_instance:
                if "meeting_id" in id_or_instance:
                    meeting_ids.add(id_or_instance["meeting_id"])
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
                lock_result=False,
            )
            meeting_ids.update(user.get("meeting_ids", []))
            committees_manager.update(set(user.get("committee_management_ids") or []))
            oml_right = user.get("organization_management_level", "")
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting",
                    list(meeting_ids),
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
            meeting_ids = {
                meeting_id
                for mids in committees_to_meetings.values()
                for meeting_id in mids
            }
            if not meeting_ids or not self.check_for_admin_in_all_meetings(
                instance_id, meeting_ids
            ):
                raise MissingPermission(
                    {
                        OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                        **{
                            Permissions.User.CAN_UPDATE: meeting_id
                            for meeting_id in meeting_ids
                        },
                    }
                )

    def check_for_admin_in_all_meetings(
        self,
        instance_id: int,
        b_meeting_ids: set[int] | None = None,
    ) -> bool:
        """
        This is used during a permission check for scope request, user.update/create with payload fields A and F and during
        user altering actions like user.delete or set_default_password.
        Checks if the requesting user has permissions to manage participants in all of requested users meetings
        but requested user doesn't have any of these permissions. See backend issue 2522 on github for more details.
        Also checks requested user has no committee management rights if a dict was provided instead of an id.
        An ID will be provided during user deletion.
        Returns true if permissions are given. False if not. Raises no Exceptions.
        """
        if not self._check_not_committee_manager(instance_id):
            return False

        if not (
            intersection_meetings := self._collect_intersected_meetings(b_meeting_ids)
        ):
            return False
        assert isinstance(intersection_meetings, dict)
        admin_meeting_users = self._collect_admin_meeting_users(intersection_meetings)
        meeting_to_admin_users = self._collect_admin_users(admin_meeting_users)
        return self._analyze_meetings(meeting_to_admin_users, instance_id)

    def _check_not_committee_manager(self, instance_id: int) -> bool:
        if not (hasattr(self, "name") and self.name == "user.create"):
            if self.datastore.get(
                fqid_from_collection_and_id("user", instance_id),
                ["committee_management_ids"],
                lock_result=False,
                use_changed_models=False,
            ).get("committee_management_ids", []):
                return False
        return True

    def _collect_intersected_meetings(
        self, b_meeting_ids: set[int] | None
    ) -> dict[int, Any] | bool:
        """Takes the meeting ids to find intersections with the requesting users meetings. Returns False if this is not possible."""
        if not b_meeting_ids:
            if not hasattr(self, "instance_committee_meeting_ids"):
                return False
            if not (
                b_meeting_ids := {
                    m_id
                    for m_ids in self.instance_committee_meeting_ids.values()
                    for m_id in m_ids
                }
            ):
                return False
        # During participant import there is no permstore.
        if hasattr(self, "permstore"):
            a_meeting_ids = (
                self.permstore.user_meetings
            )  # returns only admin level meetings
        elif not (
            a_meeting_ids := set(
                self.datastore.get(
                    fqid_from_collection_and_id("user", self.user_id),
                    ["meeting_ids"],
                    lock_result=False,
                ).get("meeting_ids", [])
            )
        ):
            return False
        intersection_meeting_ids = a_meeting_ids.intersection(b_meeting_ids)
        if not b_meeting_ids.issubset(intersection_meeting_ids):
            return False
        return self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting",
                    list(intersection_meeting_ids),
                    ["admin_group_id", "group_ids"],
                )
            ],
            lock_result=False,
        ).get("meeting", {})

    def _collect_admin_meeting_users(
        self, intersection_meetings: dict[int, Any]
    ) -> set[int]:
        """
        Gets the admin groups and those groups with permission User.CAN_UPDATE and USER.CAN_MANAGE of the meetings.
        Returns a set of the groups meeting_user_ids.
        """
        group_ids = [
            group_id
            for meeting_id, meeting_dict in intersection_meetings.items()
            for group_id in meeting_dict.get("group_ids", [])
        ]
        admin_group_ids = [
            meeting_dict["admin_group_id"]
            for meeting_dict in intersection_meetings.values()
        ]
        return {
            *{
                mu_id
                for group_id, group in self.datastore.get_many(
                    [
                        GetManyRequest(
                            "group", group_ids, ["meeting_user_ids", "permissions"]
                        )
                    ],
                    lock_result=False,
                )
                .get("group", {})
                .items()
                if (
                    "user.can_update" in group.get("permissions", [])
                    or "user.can_manage" in group.get("permissions", [])
                )
                for mu_id in group.get("meeting_user_ids", [])
            },
            *{
                mu_id
                for group_id, group in self.datastore.get_many(
                    [GetManyRequest("group", admin_group_ids, ["meeting_user_ids"])],
                    lock_result=False,
                )
                .get("group", {})
                .items()
                for mu_id in group.get("meeting_user_ids", [])
            },
        }

    def _collect_admin_users(self, meeting_user_ids: set[int]) -> dict[int, set[int]]:
        """Returns the corresponding users of the groups meeting_users in a defaultdict meeting_id: user_ids."""
        meeting_to_admin_user = defaultdict(set)
        for meeting_user in (
            self.datastore.get_many(
                [
                    GetManyRequest(
                        "meeting_user",
                        list(meeting_user_ids),
                        ["user_id", "meeting_id"],
                    )
                ],
                lock_result=False,
            )
            .get("meeting_user", {})
            .values()
        ):
            meeting_to_admin_user[meeting_user["meeting_id"]].add(
                meeting_user["user_id"]
            )
        return meeting_to_admin_user

    def _analyze_meetings(
        self, meeting_to_admin_users: dict[int, set[int]], instance_id: int
    ) -> bool:
        for meeting_id, admin_users in meeting_to_admin_users.items():
            if instance_id in admin_users:
                return False
            if self.user_id not in admin_users:
                return False
        return True
