from typing import Any, Dict

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
from ....shared.exceptions import MissingPermission
from ....shared.mixins.user_scope_mixin import UserScope, UserScopeMixin
from ....shared.patterns import to_fqid
from ...action import Action


class UserScopePermissionCheckMixin(UserScopeMixin, Action):
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
            meeting = self.datastore.get(to_fqid("meeting", scope_id), ["committee_id"])
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
