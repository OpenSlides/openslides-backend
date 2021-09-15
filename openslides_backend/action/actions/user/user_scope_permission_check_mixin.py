from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
    has_perm,
)
from ....permissions.permissions import Permissions
from ....services.datastore.interface import GetManyRequest
from ....shared.exceptions import MissingPermission
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action


class UserScope(Enum):
    Meeting = auto()
    Committee = auto()
    Organization = auto()


class UserScopePermissionCheckMixin(Action):
    def check_permissions_for_scope(self, instance: Dict[str, Any]) -> None:
        """
        Checks the permissions for user-altering actions depending on the user scope.
        """
        if has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            return

        scope, scope_id = self.get_user_scope(instance["id"])
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
            meeting = self.datastore.fetch_model(
                FullQualifiedId(Collection("meeting"), scope_id), ["committee_id"]
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

    def get_user_scope(
        self, id: Optional[int] = None, instance: Optional[Dict[str, Any]] = None
    ) -> Tuple[UserScope, int]:
        """
        Returns the scope of the given user id together with the relevant scope id (either meeting, committee or organization).
        """
        meetings: List[int] = []
        meetingsd: Dict[int, int]
        committees: List[int] = []

        if instance:
            meetings = list(map(int, instance.get("group_$_ids", {}).keys()))
            committees = instance.get("committee_ids", [])
        elif id:
            user = self.datastore.fetch_model(
                FullQualifiedId(self.model.collection, id),
                ["meeting_ids", "committee_ids"],
            )
            meetings = user.get("meeting_ids", [])
            committees = user.get("committee_ids", [])
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    Collection("meeting"),
                    meetings,
                    ["committee_id", "is_active_in_organization_id"],
                )
            ]
        ).get(Collection("meeting"), {})
        meetingsd = {
            meeting_id: odict.get("committee_id")
            for meeting_id, odict in result.items()
            if odict.get("is_active_in_organization_id")
        }

        if len(meetingsd) == 1 and len(committees) == 0:
            return UserScope.Meeting, next(iter(meetingsd))
        elif len(committees) == 1:
            # make sure that all meetings belong to this committee
            if not meetingsd or all(
                committee == committees[0] for committee in meetingsd.values()
            ):
                return UserScope.Committee, committees[0]
        return UserScope.Organization, 1
