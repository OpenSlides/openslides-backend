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
                    "committee_management_ids": [1],
                },
            )
        elif scope == UserScope.Meeting:
            self.create_meeting()
            self.set_organization_management_level(None)
            self.set_user_groups(1, [3])
            self.set_group_permissions(3, [meeting_permission])
        self.set_models(
            {
                "user/777": {
                    "username": "admin_group_filler",
                    "meeting_user_ids": [666, 667],
                },
                "meeting_user/666": {
                    "group_ids": [12, 23],
                    "meeting_id": 1,
                    "user_id": 777,
                },
                "meeting_user/667": {
                    "group_ids": [12, 23],
                    "meeting_id": 2,
                    "user_id": 777,
                },
                "group/12": {"meeting_user_ids": [666]},
                "group/23": {"meeting_user_ids": [667]},
            }
        )

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
                        "group_ids": [11, 12],
                        "admin_group_id": 12,
                        "is_active_in_organization_id": 1,
                    },
                    "meeting/2": {
                        "user_ids": [111],
                        "committee_id": 2,
                        "group_ids": [22, 23],
                        "admin_group_id": 23,
                        "is_active_in_organization_id": 1,
                    },
                    "user/111": {
                        "meeting_ids": [1, 2],
                        "committee_ids": [1, 2],
                        "meeting_user_ids": [11, 22],
                    },
                    "meeting_user/11": {
                        "meeting_id": 1,
                        "user_id": 111,
                        "group_ids": [11],
                    },
                    "meeting_user/22": {
                        "meeting_id": 1,
                        "user_id": 111,
                        "group_ids": [22],
                    },
                    "group/11": {"meeting_id": 1, "meeting_user_ids": [11]},
                    "group/12": {"meeting_id": 1, "meeting_user_ids": [666]},
                    "group/22": {"meeting_id": 2, "meeting_user_ids": [22]},
                    "group/23": {"meeting_id": 2, "meeting_user_ids": [667]},
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
                        "meeting_user_ids": [11, 22],
                    },
                    "meeting_user/11": {
                        "meeting_id": 1,
                        "user_id": 111,
                        "group_ids": [11],
                    },
                    "meeting_user/22": {
                        "meeting_id": 1,
                        "user_id": 111,
                        "group_ids": [22],
                    },
                    "group/11": {"meeting_id": 1, "meeting_user_ids": [11]},
                    "group/22": {"meeting_id": 2, "meeting_user_ids": [22]},
                }
            )
        elif scope == UserScope.Meeting:
            self.set_models(
                {
                    "committee/1": {"meeting_ids": [1]},
                    "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                    "user/111": {"meeting_ids": [1], "committee_ids": [1]},
                }
            )
