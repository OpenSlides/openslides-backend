from typing import Optional

from openslides_backend.action.actions.user.user_scope_permission_check_mixin import (
    UserScope,
)
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ScopePermissionsTestMixin(BaseActionTestCase):
    def setup_admin_scope_permissions(self, scope: Optional[UserScope]) -> None:
        """
        Helper function to setup permissions for different scopes for user 1. If no scope is given, the user has no permissions.
        """
        if scope is None:
            self.set_organization_management_level(None)
        elif scope == UserScope.Organization:
            self.set_organization_management_level(
                OrganizationManagementLevel.CAN_MANAGE_USERS
            )
        elif scope == UserScope.Committee:
            self.update_model(
                "user/1",
                {
                    "organization_management_level": None,
                    "committee_$can_manage_management_level": [1],
                },
            )
        elif scope == UserScope.Meeting:
            self.create_meeting()
            self.set_organization_management_level(None)
            self.set_user_groups(1, [3])
            self.set_group_permissions(3, [Permissions.User.CAN_MANAGE])

    def setup_scoped_user(self, scope: UserScope) -> None:
        """
        Helper function to setup user 111 in different scopes.
        """
        if scope == UserScope.Organization:
            self.set_models(
                {
                    "committee/1": {"meeting_ids": [1]},
                    "committee/2": {"meeting_ids": [2]},
                    "meeting/1": {
                        "user_ids": [111],
                        "committee_id": 1,
                        "group_ids": [11],
                        "is_active_in_organization_id": 1,
                    },
                    "meeting/2": {
                        "user_ids": [111],
                        "committee_id": 2,
                        "group_ids": [22],
                        "is_active_in_organization_id": 1,
                    },
                    "user/111": {
                        "meeting_ids": [1, 2],
                        "committee_ids": [1, 2],
                        "group_$_ids": ["1", "2"],
                        "group_$1_ids": [11],
                        "group_$2_ids": [22],
                    },
                    "group/11": {"meeting_id": 1, "user_ids": [111]},
                    "group/22": {"meeting_id": 2, "user_ids": [111]},
                }
            )
        elif scope == UserScope.Committee:
            self.set_models(
                {
                    "committee/1": {"meeting_ids": [1, 2]},
                    "meeting/1": {
                        "user_ids": [111],
                        "committee_id": 1,
                        "group_ids": [11],
                        "is_active_in_organization_id": 1,
                    },
                    "meeting/2": {
                        "user_ids": [111],
                        "committee_id": 1,
                        "group_ids": [11],
                        "is_active_in_organization_id": 1,
                    },
                    "user/111": {
                        "meeting_ids": [1, 2],
                        "committee_ids": [1],
                        "group_$_ids": ["1", "2"],
                        "group_$1_ids": [11],
                        "group_$2_ids": [22],
                    },
                    "group/11": {"meeting_id": 1, "user_ids": [111]},
                    "group/22": {"meeting_id": 2, "user_ids": [111]},
                }
            )
        elif scope == UserScope.Meeting:
            self.set_models(
                {
                    "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                    "user/111": {"meeting_ids": [1], "committee_ids": [1]},
                }
            )
