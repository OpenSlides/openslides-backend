from tests.system.action.base import BaseActionTestCase

from .scope_permissions_mixin import ScopePermissionsTestMixin, UserScope


class UserGenerateNewPasswordActionTest(ScopePermissionsTestMixin, BaseActionTestCase):
    def test_correct(self) -> None:
        self.update_model("user/1", {"password": "old_pw"})
        response = self.request("user.generate_new_password", {"id": 1})
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert model.get("password") is not None
        assert self.auth.is_equals(
            model.get("default_password", ""), model.get("password", "")
        )

    def test_scope_meeting_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.generate_new_password. Missing permissions: OrganisationManagementLevel can_manage_users in organisation 1 or CommitteeManagementLevel can_manage in committee 1 or Permission user.can_manage in meeting 1",
            response.json["message"],
        )

    def test_scope_meeting_permission_in_organisation(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organisation)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("password") and user.get("default_password")

    def test_scope_meeting_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("password") and user.get("default_password")

    def test_scope_meeting_permission_in_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("password") and user.get("default_password")

    def test_scope_committee_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.generate_new_password. Missing permissions: OrganisationManagementLevel can_manage_users in organisation 1 or CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_scope_committee_permission_in_organisation(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organisation)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("password") and user.get("default_password")

    def test_scope_committee_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("password") and user.get("default_password")

    def test_scope_committee_permission_in_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.generate_new_password. Missing permissions: OrganisationManagementLevel can_manage_users in organisation 1 or CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_scope_organisation_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Organisation)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.generate_new_password. Missing permission: OrganisationManagementLevel can_manage_users in organisation 1",
            response.json["message"],
        )

    def test_scope_organisation_permission_in_organisation(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organisation)
        self.setup_scoped_user(UserScope.Organisation)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("password") and user.get("default_password")

    def test_scope_organisation_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Organisation)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.generate_new_password. Missing permission: OrganisationManagementLevel can_manage_users in organisation 1",
            response.json["message"],
        )

    def test_scope_organisation_permission_in_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Organisation)
        response = self.request("user.generate_new_password", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.generate_new_password. Missing permission: OrganisationManagementLevel can_manage_users in organisation 1",
            response.json["message"],
        )
