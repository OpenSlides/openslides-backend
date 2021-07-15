from tests.system.action.base import BaseActionTestCase

from .scope_permissions_mixin import ScopePermissionsTestMixin, UserScope


class UserDeleteActionTest(ScopePermissionsTestMixin, BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("user/111", {"username": "username_srtgb123"})
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("user/112", {"username": "username_srtgb123"})
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 400)
        model = self.get_model("user/112")
        assert model.get("username") == "username_srtgb123"

    def test_delete_correct_with_template_field(self) -> None:
        self.set_models(
            {
                "user/111": {
                    "username": "username_srtgb123",
                    "group_$_ids": ["42"],
                    "group_$42_ids": [456],
                },
                "group/456": {"meeting_id": 42, "user_ids": [111, 222]},
                "meeting/42": {"group_ids": [456], "user_ids": [111]},
            }
        )
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")
        model = self.get_model("group/456")
        assert model.get("user_ids") == [222]
        # check meeting.user_ids
        meeting = self.get_model("meeting/42")
        assert meeting.get("user_ids") == []

    def test_delete_with_speaker(self) -> None:
        self.set_models(
            {
                "user/111": {
                    "username": "username_srtgb123",
                    "speaker_$_ids": ["1"],
                    "speaker_$1_ids": [15],
                },
                "meeting/1": {},
                "speaker/15": {"user_id": 111, "meeting_id": 1},
            }
        )
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")
        self.assert_model_deleted("speaker/15")

    def test_delete_scope_meeting_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 1 or Permission user.can_manage in meeting 1",
            response.json["message"],
        )

    def test_delete_scope_meeting_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")

    def test_delete_scope_meeting_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")

    def test_delete_scope_meeting_permission_in_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")

    def test_delete_scope_committee_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_delete_scope_committee_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")

    def test_delete_scope_committee_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")

    def test_delete_scope_committee_permission_in_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_delete_scope_organization_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
            response.json["message"],
        )

    def test_delete_scope_organization_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")

    def test_delete_scope_organization_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
            response.json["message"],
        )

    def test_delete_scope_organization_permission_in_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
            response.json["message"],
        )
