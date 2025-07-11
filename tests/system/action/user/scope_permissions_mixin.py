from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permission, Permissions
from openslides_backend.shared.mixins.user_scope_mixin import UserScope
from tests.system.action.base import BaseActionTestCase


class ScopePermissionsTestMixin(BaseActionTestCase):
    def setup_admin_scope_permissions(
        self,
        scope: UserScope | None,
        meeting_permission: Permission = Permissions.User.CAN_MANAGE,
    ) -> None:
        """
        Helper function to setup permissions for different scopes for user 1. If no scope is given, the user has no permissions.
        """
        self.create_meeting()
        self.create_meeting(4)
        if scope is None:
            self.set_organization_management_level(None)
        elif scope == UserScope.Organization:
            self.set_organization_management_level(
                OrganizationManagementLevel.CAN_MANAGE_USERS
            )
        elif scope == UserScope.Committee:
            self.set_models(
                {
                    "user/1": {
                        "organization_management_level": None,
                        "committee_management_ids": [60],
                    },
                    "committee/60": {"manager_ids": [1]},
                }
            )
        elif scope == UserScope.Meeting:
            self.set_organization_management_level(None)
            self.set_user_groups(1, [3])
            self.set_group_permissions(3, [meeting_permission])
        self.set_models(
            {
                "user/777": {
                    "username": "admin_group_filler",
                },
            }
        )
        self.set_user_groups(777, [2, 5])

    def setup_scoped_user(self, scope: UserScope) -> None:
        """
        Helper function to setup user 111 in different scopes.
        """
        if scope == UserScope.Organization:
            self.set_models(
                {
                    "meeting/1": {
                        "group_ids": [1, 2, 3, 11],
                    },
                    "meeting/4": {
                        "group_ids": [4, 5, 6, 22],
                    },
                    "user/111": {
                        "username": "user111",
                        "meeting_user_ids": [11, 22],
                    },
                    "meeting_user/11": {
                        "meeting_id": 1,
                        "user_id": 111,
                        "group_ids": [11],
                    },
                    "meeting_user/22": {
                        "meeting_id": 4,
                        "user_id": 111,
                        "group_ids": [22],
                    },
                    "group/11": {
                        "name": "group11",
                        "meeting_id": 1,
                        "meeting_user_ids": [11],
                    },
                    "group/22": {
                        "name": "group22",
                        "meeting_id": 4,
                        "meeting_user_ids": [22],
                    },
                }
            )
        elif scope == UserScope.Committee:
            self.set_models(
                {
                    "meeting/1": {
                        "group_ids": [11],
                    },
                    "meeting/4": {
                        "committee_id": 60,
                        "group_ids": [11],
                    },
                    "user/111": {
                        "username": "user111",
                        "meeting_user_ids": [11, 22],
                    },
                    "meeting_user/11": {
                        "meeting_id": 1,
                        "user_id": 111,
                        "group_ids": [11],
                    },
                    "meeting_user/22": {
                        "meeting_id": 4,
                        "user_id": 111,
                        "group_ids": [22],
                    },
                    "group/11": {
                        "name": "group11",
                        "meeting_id": 1,
                        "meeting_user_ids": [11],
                    },
                    "group/22": {
                        "name": "group22",
                        "meeting_id": 4,
                        "meeting_user_ids": [22],
                    },
                }
            )
        elif scope == UserScope.Meeting:
            self.set_models(
                {
                    "user/111": {
                        "username": "user111",
                    },
                    "meeting_user/1111": {
                        "user_id": 111,
                        "meeting_id": 1,
                        "group_ids": [1],
                    },
                    "group/1": {"meeting_user_ids": [1111]},
                }
            )
