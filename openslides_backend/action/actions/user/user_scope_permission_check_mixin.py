from enum import Enum, auto
from typing import Any, Dict, Tuple

from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganisationManagementLevel,
)
from ....permissions.permission_helper import (
    has_committee_management_level,
    has_organisation_management_level,
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
    Organisation = auto()


class UserScopePermissionCheckMixin(Action):
    def check_permissions_for_scope(self, instance: Dict[str, Any]) -> None:
        """
        Checks the permissions for user-altering actions depending on the user scope.
        """
        if has_organisation_management_level(
            self.datastore, self.user_id, OrganisationManagementLevel.CAN_MANAGE_USERS
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
                        OrganisationManagementLevel.CAN_MANAGE_USERS: 1,
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
                        OrganisationManagementLevel.CAN_MANAGE_USERS: 1,
                        CommitteeManagementLevel.CAN_MANAGE: meeting["committee_id"],
                        Permissions.User.CAN_CHANGE_OWN_PASSWORD: scope_id,
                    }
                )
        else:
            raise MissingPermission({OrganisationManagementLevel.CAN_MANAGE_USERS: 1})

    def get_user_scope(self, id: int) -> Tuple[UserScope, int]:
        """
        Returns the scope of the given user id together with the relevant scope id (either meeting, committee or organisation).
        """
        user = self.datastore.fetch_model(
            FullQualifiedId(self.model.collection, id), ["meeting_ids", "committee_ids"]
        )
        meetings = user.get("meeting_ids", [])
        committees = user.get("committee_ids", [])
        if len(meetings) == 1 and len(committees) == 0:
            return UserScope.Meeting, meetings[0]
        elif len(committees) == 1:
            # make sure that all meetings belong to this committee
            if meetings:
                result = self.datastore.get_many(
                    [GetManyRequest(Collection("meeting"), meetings, ["committee_id"])]
                )
                db_meetings = result.get(Collection("meeting"), {}).values()
            if not meetings or all(
                meeting["committee_id"] == committees[0] for meeting in db_meetings
            ):
                return UserScope.Committee, committees[0]
        return UserScope.Organisation, 1
