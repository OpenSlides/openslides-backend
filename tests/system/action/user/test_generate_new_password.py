from openslides_backend.action.util.crypto import PASSWORD_CHARS
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permission, Permissions
from tests.system.action.base import BaseActionTestCase

from .scope_permissions_mixin import ScopePermissionsTestMixin, UserScope


class UserGenerateNewPasswordActionTest(ScopePermissionsTestMixin, BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.reset_redis()

    def test_correct(self) -> None:
        self.update_model("user/1", {"password": "old_pw"})
        response = self.request("user.generate_new_password", {"id": 1})
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert (hash := model.get("password")) is not None
        assert (password := model.get("default_password")) is not None
        assert all(char in PASSWORD_CHARS for char in password)
        assert self.auth.is_equal(password, hash)
        self.assert_logged_out()

    def test_scope_meeting_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.generate_new_password. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 60 or Permission user.can_update in meeting 1",
            response.json["message"],
        )

    def test_scope_meeting_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("password") and user.get("default_password")
        self.assert_logged_in()

    def test_scope_meeting_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("password") and user.get("default_password")
        self.assert_logged_in()

    def test_scope_meeting_permission_in_meeting(self) -> None:
        self.assert_scope_meeting_permission_in_meeting(Permissions.User.CAN_UPDATE)

    def test_scope_meeting_permission_in_meeting_with_permission_parent(self) -> None:
        self.assert_scope_meeting_permission_in_meeting(Permissions.User.CAN_MANAGE)

    def assert_scope_meeting_permission_in_meeting(
        self, permission: Permission
    ) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting, permission)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("password") and user.get("default_password")
        self.assert_logged_in()

    def test_scope_committee_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.generate_new_password. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 60",
            response.json["message"],
        )

    def test_scope_committee_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("password") and user.get("default_password")
        self.assert_logged_in()

    def test_scope_committee_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("password") and user.get("default_password")
        self.assert_logged_in()

    def test_scope_committee_permission_in_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.generate_new_password. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 60",
            response.json["message"],
        )

    def test_scope_organization_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.generate_new_password. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 4",
            response.json["message"],
        )

    def test_scope_organization_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("password") and user.get("default_password")
        self.assert_logged_in()

    def test_scope_organization_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.set_models(
            {
                "user/111": {"id": 111, "username": "fritz"},
            }
        )
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.generate_new_password. Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
            response.json["message"],
        )

    def test_scope_multi_committee_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("password") and user.get("default_password")
        self.assert_logged_in()

    def test_scope_organization_permission_in_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.generate_new_password. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 4",
            response.json["message"],
        )

    def test_scope_superadmin_with_oml_usermanager(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Meeting)
        self.set_models(
            {
                "user/111": {
                    "organization_management_level": OrganizationManagementLevel.SUPERADMIN
                }
            }
        )
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.generate_new_password. Missing permission: OrganizationManagementLevel superadmin in organization 1",
            response.json["message"],
        )

    def test_saml_user_error(self) -> None:
        self.update_model("user/1", {"password": "pw", "saml_id": "111"})
        response = self.request("user.generate_new_password", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "user 111 is a Single Sign On user and has no local OpenSlides password.",
            response.json["message"],
        )
