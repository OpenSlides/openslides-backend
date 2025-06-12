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
    ) -> tuple[UserScope, int, str, dict[int, list[int]], bool, int | None]:
        """
        Parameter id_or_instance: id for existing user or instance for user to create
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
        meeting_ids: set[int] = set()
        committees_manager: set[int] = set()
        home_committee_id: int | None
        if isinstance(id_or_instance, dict):
            if "group_ids" in id_or_instance:
                if "meeting_id" in id_or_instance:
                    meeting_ids.add(id_or_instance["meeting_id"])
            committees_manager.update(
                set(id_or_instance.get("committee_management_ids", []))
            )
            oml_right = id_or_instance.get("organization_management_level", "")
            home_committee_id = id_or_instance.get("home_committee_id")
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
            meeting_ids.update(user.get("meeting_ids", []))
            committees_manager.update(set(user.get("committee_management_ids") or []))
            oml_right = user.get("organization_management_level", "")
            home_committee_id = user.get("home_committee_id")

        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting",
                    list(meeting_ids),
                    ["committee_id", "is_active_in_organization_id"],
                )
            ]
        ).get("meeting", {})

        meetings_committee: dict[int, int] = {}
        active_meetings_committee: dict[int, int] = {}

        for meeting_id, meeting_data in result.items():
            committee_id = meeting_data["committee_id"]
            meetings_committee[meeting_id] = committee_id
            if meeting_data.get("is_active_in_organization_id"):
                active_meetings_committee[meeting_id] = committee_id

        committee_meetings, committees = self._get_committee_meetings_and_committees(
            meetings_committee, committees_manager
        )
        active_committee_meetings, active_committees = (
            self._get_committee_meetings_and_committees(
                active_meetings_committee, committees_manager
            )
        )

        user_in_archived_meetings_only = (
            len(active_committee_meetings) == 0 and len(committee_meetings) > 0
        )

        if home_committee_id:
            return (
                UserScope.Committee,
                home_committee_id,
                oml_right,
                active_committee_meetings,
                user_in_archived_meetings_only,
                home_committee_id,
            )
        if len(active_meetings_committee) == 1 and len(active_committees) == 1:
            return (
                UserScope.Meeting,
                next(iter(active_meetings_committee)),
                oml_right,
                active_committee_meetings,
                user_in_archived_meetings_only,
                home_committee_id,
            )
        if len(committees) == 1:
            return (
                UserScope.Committee,
                next(iter(committees)),
                oml_right,
                committee_meetings,
                user_in_archived_meetings_only,
                home_committee_id,
            )
        return (
            UserScope.Organization,
            1,
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
        With check_user_oml_always=True it will be checked whether the request user
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
            if user_in_archived_meetings_only:
                raise MissingPermission(
                    {
                        OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                        CommitteeManagementLevel.CAN_MANAGE: {
                            ci for ci in committees_to_meetings.keys()
                        },
                    }
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
        * requesting user has those permissions in all of those meetings
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
        Gets the requested users meetings if these are subset of requesting user. Returns False if this is not possible.
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

    def _get_committee_meetings_and_committees(
        self, meetings_committee: dict[int, int], committees_manager: set[int]
    ) -> tuple[dict[int, list[int]], set[int]]:
        committees = committees_manager | set(meetings_committee.values())
        committee_meetings: dict[int, Any] = defaultdict(list)
        for meeting, committee in meetings_committee.items():
            committee_meetings[committee].append(meeting)
        for committee in committees:
            if committee not in committee_meetings.keys():
                committee_meetings[committee] = None
        return committee_meetings, committees

    def _collect_admin_meeting_users(self, meetings: dict[int, Any]) -> set[int]:
        """
        Gets the admin groups and those groups with permission User.CAN_UPDATE and USER.CAN_MANAGE of the meetings.
        Returns a set of the groups meeting_user_ids.
        """
        group_ids = [
            group_id
            for meeting_id, meeting_dict in meetings.items()
            for group_id in meeting_dict.get("group_ids", [])
        ]
        return {
            mu_id
            for group_id, group in self.datastore.get_many(
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
            .items()
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
        Compares the users of admin meeting users of all meetings with the ids of requested user and requesting user.
        Requesting user must be admin in all meetings. Requested user cannot be admin in any.
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
