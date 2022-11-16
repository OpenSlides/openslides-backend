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
from ....shared.patterns import fqid_from_collection_and_id
from ...action import Action


class UserScopePermissionCheckMixin(UserScopeMixin, Action):
    def check_permissions_for_scope(
        self, instance: Dict[str, Any], check_user_oml_always: bool
    ) -> None:
        """
        Checks the permissions for user-altering actions depending on the user scope.
        With check_user_oml_always = True it will be checked, whether the request user
        has at minimum the same OML-level than the requested user to pass.
        Reason: A user with OML-level-permission has scope meeting or committee, if
        he belongs to only 1 meeting or 1 committee.
        """
        scope, scope_id, user_oml = self.get_user_scope(instance["id"])
        if (
            check_user_oml_always
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
