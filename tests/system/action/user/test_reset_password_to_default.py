from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permission, Permissions
from tests.system.action.base import BaseActionTestCase

from .scope_permissions_mixin import ScopePermissionsTestMixin, UserScope


class UserResetPasswordToDefaultTest(ScopePermissionsTestMixin, BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.reset_redis()
        self.password = "pw_quSEYapV"
        self.create_model(
            "user/111",
            {"username": "username_srtgb123", "default_password": self.password},
        )

    def test_reset_password_to_default(self) -> None:
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.password, model.get("password", ""))
        self.assert_logged_in()

    def test_reset_with_logout(self) -> None:
        self.set_models({"user/1": {"default_password": self.password}})
        response = self.request("user.reset_password_to_default", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_logged_out()

    def test_scope_meeting_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.reset_password_to_default. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 1 or Permission user.can_update in meeting 1",
            response.json["message"],
        )

    def test_scope_meeting_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.password, model.get("password", ""))
        self.assert_logged_in()

    def test_scope_meeting_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.password, model.get("password", ""))
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
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.password, model.get("password", ""))
        self.assert_logged_in()

    def test_scope_committee_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.reset_password_to_default. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_scope_committee_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.password, model.get("password", ""))
        self.assert_logged_in()

    def test_scope_committee_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.password, model.get("password", ""))
        self.assert_logged_in()

    def test_scope_committee_permission_in_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.reset_password_to_default. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_scope_organization_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.reset_password_to_default. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 2",
            response.json["message"],
        )

    def test_scope_organization_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.password, model.get("password", ""))
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
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.reset_password_to_default. Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
            response.json["message"],
        )

    def test_scope_multi_committee_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.password, model.get("password", ""))
        self.assert_logged_in()

    def test_scope_organization_permission_in_one_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.reset_password_to_default. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 2",
            response.json["message"],
        )

    def test_scope_organization_permission_in_all_meetings(self) -> None:
        self.setup_scope_organization_with_permission_in_all_meetings()
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equal(self.password, model.get("password", ""))
        self.assert_logged_in()

    def test_scope_organization_permission_in_meeting_archived_meetings_in_different_committees(
        self,
    ) -> None:
        self.setup_archived_meetings_in_different_committees()
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.reset_password_to_default. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committees {60, 63}",
            response.json["message"],
        )

    def test_scope_superadmin_with_oml_usermanager(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Organization)
        self.set_models(
            {
                "user/111": {
                    "organization_management_level": OrganizationManagementLevel.SUPERADMIN
                }
            }
        )
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.reset_password_to_default. Missing permission: OrganizationManagementLevel superadmin in organization 1",
            response.json["message"],
        )

    def test_reset_password_to_default_saml_id_error(self) -> None:
        self.update_model("user/111", {"saml_id": "111"})
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 400)
        self.assertIn(
            "user 111 is a Single Sign On user and has no local OpenSlides password.",
            response.json["message"],
        )
