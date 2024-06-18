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
            "You are not allowed to perform action user.set_password. Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
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
        self.setup_scoped_user(UserScope.Organization)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.set_password. Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
            response.json["message"],
        )

    def test_scope_organization_permission_in_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request(
            "user.set_password", {"id": 111, "password": self.PASSWORD}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.set_password. Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
            response.json["message"],
        )

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
