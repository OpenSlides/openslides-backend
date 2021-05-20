from typing import Optional

from openslides_backend.action.actions.user.user_scope_permission_check_mixin import (
    UserScope,
)
from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganisationManagementLevel,
)
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ScopePermissionsTestMixin(BaseActionTestCase):
    def setup_admin_scope_permissions(self, scope: Optional[UserScope]) -> None:
        """
        Helper function to setup permissions for different scopes for user 1. If no scope is given, the user has no permissions.
        """
        if scope is None:
            self.set_management_level(None)
        elif scope == UserScope.Organisation:
            self.set_management_level(OrganisationManagementLevel.CAN_MANAGE_USERS)
        elif scope == UserScope.Committee:
            self.update_model(
                "user/1",
                {
                    "organisation_management_level": None,
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                },
            )
        elif scope == UserScope.Meeting:
            self.create_meeting()
            self.set_management_level(None)
            self.set_user_groups(1, [3])
            self.set_group_permissions(3, [Permissions.User.CAN_MANAGE])

    def setup_scoped_user(self, scope: UserScope) -> None:
        """
        Helper function to setup user 111 in different scopes.
        """
        if scope == UserScope.Organisation:
            self.set_models(
                {
                    "meeting/1": {"committee_id": 1},
                    "user/111": {"meeting_ids": [1], "committee_ids": [2]},
                }
            )
        elif scope == UserScope.Committee:
            self.set_models(
                {
                    "meeting/1": {"committee_id": 1},
                    "user/111": {"meeting_ids": [1], "committee_ids": [1]},
                }
            )
        elif scope == UserScope.Meeting:
            self.set_models(
                {"meeting/1": {"committee_id": 1}, "user/111": {"meeting_ids": [1]}}
            )
