from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permission, Permissions
from tests.system.action.base import BaseActionTestCase

from .scope_permissions_mixin import ScopePermissionsTestMixin, UserScope


class UserSetPasswordActionTest(ScopePermissionsTestMixin, BaseActionTestCase):
    PASSWORD = "password"

    def setUp(self) -> None:
        super().setUp()
        self.reset_redis()

    def test_update_correct(self) -> None:
        self.create_model("user/2", {"password": "old_pw"})
        response = self.request(
            "user.set_password", {"id": 2, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/2")
        assert self.auth.is_equal(self.PASSWORD, model.get("password", ""))
        self.assert_history_information("user/2", ["Password changed"])
        self.assert_logged_in()

    def test_two_meetings(self) -> None:
        self.create_meeting()
        self.create_meeting(4)  # meeting 4
        user_id = self.create_user("test", group_ids=[1])
        self.login(user_id)
        self.set_models(
            {
                "user/111": {"password": "old_pw"},
                "meeting_user/666": {
                    "group_ids": [12, 23],
                    "meeting_id": 12,
                    "user_id": 1,
                },
            }
        )
        self.update_model(
            "user/1",
            {"meeting_user_ids": [666]},
        )
        # only to make sure every meeting has an admin at all times
        self.set_user_groups(1, [2, 5])
        # Admin groups of meeting/1 for test user meeting/2 as normal user
        self.set_user_groups(user_id, [2, 4])
        # 111 into both meetings
        self.set_user_groups(111, [1, 4])
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.set_password. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 4",
            response.json["message"],
        )
        model = self.get_model("user/111")
        assert "old_pw" == model.get("password", "")
        # Admin groups of meeting/1 for test user
        self.set_user_groups(user_id, [2])
        # 111 into both meetings
        self.set_user_groups(111, [1, 4])
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.set_password. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 4",
            response.json["message"],
        )
        model = self.get_model("user/111")
        assert "old_pw" == model.get("password", "")
        # Admin groups of meeting/1 and meeting/4 for test user
        self.set_user_groups(user_id, [2, 5])
        # 111 into both meetings
        self.set_user_groups(111, [1, 4])
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.PASSWORD, model.get("password", ""))
        self.assert_history_information("user/111", ["Password changed"])

    def test_update_correct_default_case(self) -> None:
        self.update_model("user/1", {"password": "old_pw"})
        response = self.request(
            "user.set_password",
            {"id": 1, "password": self.PASSWORD, "set_as_default": True},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert self.auth.is_equal(self.PASSWORD, model.get("password", ""))
        assert self.PASSWORD == model.get("default_password", "")
        self.assert_logged_out()

    def test_scope_meeting_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.set_password. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 1 or Permission user.can_update in meeting 1",
            response.json["message"],
        )

    def test_scope_meeting_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.PASSWORD, model.get("password", ""))
        self.assert_logged_in()

    def test_scope_meeting_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.PASSWORD, model.get("password", ""))
        self.assert_logged_in()

    def test_scope_meeting_permission_in_meeting(self) -> None:
        self.assert_scope_meeting_permission_in_meeting(Permissions.User.CAN_UPDATE)

    def test_scope_meeting_permission_in_meeting_with_permission_parent(self) -> None:
        self.assert_scope_meeting_permission_in_meeting(Permissions.User.CAN_MANAGE)

    def assert_scope_meeting_permission_in_meeting(
        self, permission: Permission
    ) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting, permission)
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.PASSWORD, model.get("password", ""))
        self.assert_logged_in()

    def test_scope_committee_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.set_password. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_scope_committee_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.PASSWORD, model.get("password", ""))
        self.assert_logged_in()

    def test_scope_committee_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.PASSWORD, model.get("password", ""))
        self.assert_logged_in()

    def test_scope_committee_permission_in_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.set_password. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_scope_organization_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.set_password. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 2",
            response.json["message"],
        )

    def test_scope_organization_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.PASSWORD, model.get("password", ""))
        self.assert_logged_in()

    def test_scope_organization_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.set_models(
            {
                "committee/1": {"meeting_ids": [1]},
                "committee/2": {"meeting_ids": [2]},
                "meeting/1": {
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "meeting/2": {
                    "committee_id": 2,
                    "is_active_in_organization_id": 1,
                },
                "user/111": {"id": 111},
                "group/11": {"meeting_id": 1},
                "group/22": {"meeting_id": 2},
            }
        )
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.set_password. Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
            response.json["message"],
        )

    def test_scope_multi_committee_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.PASSWORD, model.get("password", ""))
        self.assert_logged_in()

    def test_scope_organization_permission_in_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.set_password. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 2",
            response.json["message"],
        )

    def test_scope_organization_permission_in_meeting_archived_meetings_in_different_committees(
        self,
    ) -> None:
        error_message = self.prepare_archived_meetings_in_different_commitees(
            "set_password"
        )
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 403)
        self.assertIn(error_message, response.json["message"])

    def test_scope_superadmin_with_oml_usermanager(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Organization)
        self.set_models(
            {
                "user/111": {
                    "organization_management_level": OrganizationManagementLevel.SUPERADMIN
                }
            }
        )
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.set_password. Missing permission: OrganizationManagementLevel superadmin in organization 1",
            response.json["message"],
        )

    def test_saml_id_error(self) -> None:
        self.create_model("user/2", {"password": "pw", "saml_id": "111"})
        response = self.request(
            "user.set_password", {"id": 2, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "user 111 is a Single Sign On user and has no local OpenSlides password.",
            response.json["message"],
        )
