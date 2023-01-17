from enum import Enum
from typing import Any, Dict, Optional, Set, Tuple, cast

from openslides_backend.shared.base_service_provider import BaseServiceProvider

from ...permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ...permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
    has_perm,
)
from ...permissions.permissions import Permissions
from ...services.datastore.interface import GetManyRequest
from ..exceptions import MissingPermission, ServiceException
from ..patterns import fqid_from_collection_and_id


class UserScope(int, Enum):
    Meeting = 1
    Committee = 2
    Organization = 3


class UserScopeMixin(BaseServiceProvider):
    def get_user_scope(
        self, id_: Optional[int] = None, instance: Optional[Dict[str, Any]] = None
    ) -> Tuple[UserScope, int, str]:
        """
        Returns the scope of the given user id together with the relevant scope id (either meeting, committee or organization).
        and the oml-level of the user as string (Empty string, if no)
        """
        meetings: Set[int] = set()
        committees_manager: Set[int] = set()
        if not instance and not id_:
            raise ServiceException("There is no user_id given to get the user_scope!")
        if instance:
            if "group_ids" in instance:
                if "meeting_id" in instance:
                    meetings.add(instance["meeting_id"])
                else:
                    meeting_user = self.datastore.get(
                        fqid_from_collection_and_id("meeting_user", instance["id"]),
                        ["meeting_id"],
                    )
                    meetings.add(meeting_user["meeting_id"])
            committees_manager.update(set(instance.get("committee_management_ids", [])))
            oml_right = instance.get("organization_management_level", "")
        if id_:
            user = self.datastore.get(
                fqid_from_collection_and_id("user", id_),
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
        committees_of_meetings = set(
            meeting_data.get("committee_id")
            for _, meeting_data in result.items()
            if meeting_data.get("is_active_in_organization_id")
        )
        committees = list(committees_manager | committees_of_meetings)
        meetings_committee = {
            meeting_id: meeting_data.get("committee_id")  # type: ignore
            for meeting_id, meeting_data in result.items()
            if meeting_data.get("is_active_in_organization_id")
        }
        if len(meetings_committee) == 1 and len(committees) == 1:
            return UserScope.Meeting, next(iter(meetings_committee)), oml_right
        elif len(committees) == 1:
            return UserScope.Committee, cast(int, committees[0]), oml_right
        return UserScope.Organization, 1, oml_right

    def check_permissions_for_scope(
        self, id: int, always_check_user_oml: bool = True
    ) -> None:
        """
        Checks the permissions for user-altering actions depending on the user scope.
        With check_user_oml_always=True it will be checked whether the request user
        has at minimum the same OML-level than the requested user to pass.
        Reason: A user with OML-level-permission has scope "meeting" or "committee" if
        he belongs to only 1 meeting or 1 committee.
        """
        scope, scope_id, user_oml = self.get_user_scope(id)
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
                self.datastore, self.user_id, Permissions.User.CAN_MANAGE, scope_id
            ):
                raise MissingPermission(
                    {
                        OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                        CommitteeManagementLevel.CAN_MANAGE: meeting["committee_id"],
                        Permissions.User.CAN_MANAGE: scope_id,
                    }
                )
        else:
            raise MissingPermission({OrganizationManagementLevel.CAN_MANAGE_USERS: 1})
