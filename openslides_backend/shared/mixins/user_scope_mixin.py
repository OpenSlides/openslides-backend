from enum import StrEnum
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
from ...services.database.interface import GetManyRequest
from ..exceptions import MissingPermission
from ..patterns import fqid_from_collection_and_id


class UserScope(StrEnum):
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
    ) -> tuple[UserScope, int, str, dict[int, list[int]], bool, int | None]:
        """
        Parameter id_or_instance: id for existing user or instance for user creating and altering actions.
        Returns in the tuple:
        * the scope of the given user id
        * the relevant scope id (either meeting, committee or organization id
            depending on scope)
        * the OML level of the user as string (empty string if the user has none)
        * the ids of all committees that the user is either a manager in or a member
            of together with the respective meetings the user is part of
        * whether the user is only in archived meetings
        * his home_committee_id.
        A committee can have no meetings if the user just has committee management rights and is
        not part of any of its meetings.
        """
        meeting_ids: list[int] = []
        if isinstance(id_or_instance, dict):
            user = id_or_instance
            if "group_ids" in user and "meeting_id" in user:
                meeting_ids.append(user["meeting_id"])
        else:
            user = self.datastore.get(
                fqid_from_collection_and_id("user", id_or_instance),
                [
                    "meeting_ids",
                    "organization_management_level",
                    "committee_management_ids",
                    "home_committee_id",
                ],
                lock_result=False,
            )
            meeting_ids += user.get("meeting_ids", [])
        committees_manager = set(user.get("committee_management_ids") or [])
        oml_right = user.get("organization_management_level", "")
        home_committee_id: int | None = user.get("home_committee_id")

        (
            user_scope,
            scope_id,
            committee_meetings,
            user_in_archived_meetings_only,
        ) = self.calculate_scope_data(
            meeting_ids, committees_manager, home_committee_id
        )

        return (
            user_scope,
            scope_id,
            oml_right,
            committee_meetings,
            user_in_archived_meetings_only,
            home_committee_id,
        )

    def check_permissions_for_scope(
        self,
        instance_id: int,
        always_check_user_oml: bool = True,
        meeting_permission: Permission = Permissions.User.CAN_MANAGE,
    ) -> None:
        """
        Checks the permissions for user-altering actions depending on the user scope.
        With always_check_user_oml=True it will be checked whether the request user
        has at minimum the same OML-level than the requested user to pass.
        Reason: A user with OML-level-permission has scope "meeting" or "committee" if
        he belongs to only 1 meeting or 1 committee.
        """
        (
            scope,
            scope_id,
            user_oml,
            committees_to_meetings,
            user_in_archived_meetings_only,
            _,
        ) = self.get_user_scope(instance_id)

        if self._check_oml_levels(always_check_user_oml, user_oml):
            return
        if scope == UserScope.Committee:
            self._check_permissions_for_scope_committee(scope_id)
        elif scope == UserScope.Meeting:
            self._check_permissions_for_scope_meeting(scope_id, meeting_permission)
        else:
            self._check_permissions_for_scope_organization(
                committees_to_meetings, instance_id, user_in_archived_meetings_only
            )

    def check_for_admin_in_all_meetings(
        self,
        instance_id: int,
        b_meeting_ids: set[int] | None = None,
    ) -> bool:
        """
        This function checks the special permission condition for scope request, user.update/create with
        payload fields A and F and other user altering actions like user.delete or set_default_password.
        This function returns true if:
        * requested user is no committee manager and
        * requested user doesn't have any admin/user.can_update/user.can_manage rights in his meetings and
        * request user has those permissions in all of those meetings
        """
        if not self._check_not_committee_manager(instance_id):
            return False

        if not (meetings := self._get_meetings_if_subset(b_meeting_ids)):
            return False
        admin_meeting_users = self._collect_admin_meeting_users(meetings)
        return self._analyze_meeting_admins(admin_meeting_users, meetings)

    def _check_not_committee_manager(self, instance_id: int) -> bool:
        """
        Helper function used in method check_for_admin_in_all_meetings.
        Checks that requested user is not a committee manager.
        """
        if not (hasattr(self, "name") and self.name == "user.create"):
            if self.datastore.get(
                fqid_from_collection_and_id("user", instance_id),
                ["committee_management_ids"],
                lock_result=False,
                use_changed_models=False,
            ).get("committee_management_ids", []):
                return False
        return True

    def _get_meetings_if_subset(self, b_meeting_ids: set[int] | None) -> dict[int, Any]:
        """
        Helper function used in method check_for_admin_in_all_meetings.
        Returns:
        * Requested user's meetings if these are subset of request user's meetings.
        * Empty dict if either user has no meetings or the subset condition is not met.
        """
        if not b_meeting_ids and not (
            b_meeting_ids := {
                m_id
                for m_ids in self.instance_committee_meeting_ids.values()
                for m_id in m_ids
            }
        ):
            return {}
        if not (
            a_meeting_ids := set(
                self.datastore.get(
                    fqid_from_collection_and_id("user", self.user_id),
                    ["meeting_ids"],
                    lock_result=False,
                ).get("meeting_ids", [])
            )
        ):
            return {}
        if not b_meeting_ids.issubset(a_meeting_ids):
            return {}
        return self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting",
                    list(b_meeting_ids),
                    ["admin_group_id", "group_ids"],
                )
            ],
            lock_result=False,
        ).get("meeting", {})

    def calculate_scope_data(
        self,
        meeting_ids: list[int],
        committees_manager: set[int],
        home_committee_id: int | None,
    ) -> tuple[UserScope, int, dict[int, list[int]], bool]:
        """
        Helper function used in method get_user_scope.
        Params and return values contain data about the requested user.

        Based on the meeting_ids and committees_manager calculates user scope,
        retrieves its id and defines value for user_in_archived_meetings_only.

        If user is in the meeting scope, limits committee_meetings to the
        active meetings only.
        """
        (
            committee_meetings,
            active_committee_meetings,
            active_meetings_committee,
        ) = self._get_meetings_committees_maps(meeting_ids, committees_manager)

        user_scope, scope_id = self._get_user_scope_and_scope_id(
            home_committee_id,
            active_meetings_committee,
            active_committee_meetings,
            committee_meetings,
        )
        user_committee_meetings = (
            active_committee_meetings
            if user_scope == UserScope.Meeting
            else committee_meetings
        )
        user_in_archived_meetings_only = bool(
            not active_committee_meetings and committee_meetings
        )

        return (
            user_scope,
            scope_id,
            user_committee_meetings,
            user_in_archived_meetings_only,
        )

    def _get_meetings_committees_maps(
        self, meeting_ids: list[int], committees_manager: set[int]
    ) -> tuple[dict[int, list[int]], dict[int, list[int]], dict[int, int]]:
        """
        Helper function used in method calculate_scope_data.

        Generates data used for calculating scope details. Builds
        committees-meetings maps for user's all and active meetings.
        """
        meetings_committees, active_meetings_committees = (
            self._map_meetings_to_committees(meeting_ids)
        )

        committee_meetings = self._get_committee_meetings_map(
            meetings_committees, committees_manager
        )
        active_committee_meetings = self._get_committee_meetings_map(
            active_meetings_committees, committees_manager
        )

        return (
            committee_meetings,
            active_committee_meetings,
            active_meetings_committees,
        )

    def _map_meetings_to_committees(
        self, meeting_ids: list[int]
    ) -> tuple[dict[int, int], dict[int, int]]:
        """
        Maps each meeting to its committee. Returns full and active meeting mappings.
        """
        meetings_committees: dict[int, int] = {}
        active_meetings_committees: dict[int, int] = {}

        if meeting_ids:
            raw_meetings_data = self.datastore.get_many(
                [
                    GetManyRequest(
                        "meeting",
                        meeting_ids,
                        ["committee_id", "is_active_in_organization_id"],
                    )
                ]
            ).get("meeting", {})

            for meeting_id, meeting_data in raw_meetings_data.items():
                committee_id = meeting_data["committee_id"]
                meetings_committees[meeting_id] = committee_id
                if meeting_data.get("is_active_in_organization_id"):
                    active_meetings_committees[meeting_id] = committee_id

        return meetings_committees, active_meetings_committees

    def _get_committee_meetings_map(
        self, meetings_committee: dict[int, int], committees_manager: set[int]
    ) -> dict[int, list[int]]:
        """
        Returns a mapping of user's committee IDs to the list with meeting IDs
        he is a member of.
        """
        committee_meetings: dict[int, list[int]] = {
            cid: [] for cid in committees_manager | set(meetings_committee.values())
        }
        for meeting, committee in meetings_committee.items():
            committee_meetings[committee].append(meeting)
        return committee_meetings

    def _get_user_scope_and_scope_id(
        self,
        home_committee_id: int | None,
        active_meetings_committee: dict[int, int],
        active_committee_meetings: dict[int, list[int]],
        committee_meetings: dict[int, list[int]],
    ) -> tuple[UserScope, int]:
        """
        Helper function used in method calculate_scope_data.
        Determines user's scope and scope ID.
        """
        if home_committee_id:
            return UserScope.Committee, home_committee_id

        if len(active_meetings_committee) == 1 and len(active_committee_meetings) == 1:
            return UserScope.Meeting, next(iter(active_meetings_committee))

        if len(committee_meetings) == 1:
            return UserScope.Committee, next(iter(committee_meetings))

        return UserScope.Organization, 1

    def _collect_admin_meeting_users(self, meetings: dict[int, Any]) -> set[int]:
        """
        Returns meeting_user_ids from groups linked to the given meetings that are either:
        * Admin groups for those meetings, or
        * Have User.CAN_UPDATE or User.CAN_MANAGE permissions
        """
        group_ids = [
            group_id
            for meeting_dict in meetings.values()
            for group_id in meeting_dict.get("group_ids", [])
        ]
        return {
            mu_id
            for group in self.datastore.get_many(
                [
                    GetManyRequest(
                        "group",
                        group_ids,
                        [
                            "meeting_user_ids",
                            "permissions",
                            "admin_group_for_meeting_id",
                        ],
                    )
                ],
                lock_result=False,
            )
            .get("group", {})
            .values()
            if (
                group.get("admin_group_for_meeting_id")
                or "user.can_update" in group.get("permissions", [])
                or "user.can_manage" in group.get("permissions", [])
            )
            for mu_id in group.get("meeting_user_ids", [])
        }

    def _analyze_meeting_admins(
        self,
        admin_meeting_user_ids: set[int],
        all_meetings: dict[int, Any],
    ) -> bool:
        """
        Helper function used in method check_for_admin_in_all_meetings.
        Compares the users of admin meeting users of all meetings with the ids of requested user and request user.
        Request user must be admin in all meetings. Requested user cannot be admin in any.
        """
        meeting_id_to_admin_user_ids: dict[int, set[int]] = {
            meeting_id: set() for meeting_id in all_meetings
        }
        for meeting_user in (
            self.datastore.get_many(
                [
                    GetManyRequest(
                        "meeting_user",
                        list(admin_meeting_user_ids),
                        ["user_id", "meeting_id"],
                    )
                ],
                lock_result=False,
            )
            .get("meeting_user", {})
            .values()
        ):
            meeting_id_to_admin_user_ids[meeting_user["meeting_id"]].add(
                meeting_user["user_id"]
            )
        return all(
            self.user_id in admin_users
            for admin_users in meeting_id_to_admin_user_ids.values()
        )

    def _check_oml_levels(self, always_check_user_oml: bool, user_oml: str) -> bool:
        """
        Raises error if always_check_user_oml=True and request user doesn't
        have at least the same OML as requested user.
        Otherwise passes without further scope-specific checks if request user
        has OML can_manage_users.
        """
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
            return True
        return False

    def _check_permissions_for_scope_committee(self, scope_id: int) -> None:
        """
        Passes if request user has:
        * CML can_manage in the committee of the requested user
        """
        if not has_committee_management_level(
            self.datastore,
            self.user_id,
            scope_id,
        ):
            raise MissingPermission(
                {
                    OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                    CommitteeManagementLevel.CAN_MANAGE: scope_id,
                }
            )

    def _check_permissions_for_scope_meeting(
        self, scope_id: int, meeting_permission: Permission
    ) -> None:
        """
        Passes if request user has one of:
        * meeting_permission in the meeting of the requested user
            (default - user.can_manage)
        * CML can_manage in the meeting's committee
        """
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", scope_id),
            ["committee_id"],
            lock_result=False,
        )
        if not has_committee_management_level(
            self.datastore,
            self.user_id,
            meeting["committee_id"],
        ) and not has_perm(self.datastore, self.user_id, meeting_permission, scope_id):
            raise MissingPermission(
                {
                    OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                    CommitteeManagementLevel.CAN_MANAGE: meeting["committee_id"],
                    meeting_permission: scope_id,
                }
            )

    def _check_permissions_for_scope_organization(
        self,
        committees_to_meetings: dict[int, list[int]],
        instance_id: int,
        user_in_archived_meetings_only: bool,
    ) -> None:
        """
        Passes if request user has one of:
        * CML can_manage in any committee of the requested user
        * user.can_update in all the meetings of the requested user AND
            requested user is not in archived meetings only
        """
        if get_shared_committee_management_levels(
            self.datastore,
            self.user_id,
            list(committees_to_meetings.keys()),
        ):
            return
        meeting_ids = {
            meeting_id
            for m_ids in committees_to_meetings.values()
            if m_ids
            for meeting_id in m_ids
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
        if user_in_archived_meetings_only:
            raise MissingPermission(
                {
                    OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                    CommitteeManagementLevel.CAN_MANAGE: set(
                        list(committees_to_meetings.keys())
                    ),
                }
            )
