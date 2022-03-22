from openslides_backend.permissions.management_levels import CommitteeManagementLevel
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
                    "committee_ids": [1],
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                    "committee_$can_manage_management_level": [1],
                },
                "group/456": {"meeting_id": 42, "user_ids": [111, 222]},
                "meeting/42": {
                    "group_ids": [456],
                    "user_ids": [111, 222],
                    "is_active_in_organization_id": 1,
                },
                "committee/1": {
                    "meeting_ids": [456],
                    "user_ids": [111, 222],
                    "user_$_management_level": [CommitteeManagementLevel.CAN_MANAGE],
                    "user_$can_manage_management_level": [111],
                },
            }
        )
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted(
            "user/111",
            {
                "group_$42_ids": [456],
                "committee_ids": [1],
                "committee_$can_manage_management_level": [1],
            },
        )
        self.assert_model_exists("group/456", {"user_ids": [222]})
        self.assert_model_exists("meeting/42", {"user_ids": [222]})
        self.assert_model_exists(
            "committee/1", {"user_ids": [222], "user_$can_manage_management_level": []}
        )

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

    def test_delete_with_candidate(self) -> None:
        self.set_models(
            {
                "user/111": {
                    "username": "username_srtgb123",
                    "assignment_candidate_$_ids": ["1"],
                    "assignment_candidate_$1_ids": [34],
                },
                "meeting/1": {},
                "assignment_candidate/34": {
                    "user_id": 111,
                    "meeting_id": 1,
                    "assignment_id": 123,
                },
                "assignment/123": {
                    "title": "test_assignment",
                    "candidate_ids": [34],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted(
            "user/111",
            {"assignment_candidate_$1_ids": [34], "assignment_candidate_$_ids": ["1"]},
        )
        self.assert_model_deleted(
            "assignment_candidate/34", {"assignment_id": 123, "user_id": 111}
        )
        self.assert_model_exists("assignment/123", {"candidate_ids": []})

    def test_delete_with_submitter(self) -> None:
        self.set_models(
            {
                "user/111": {
                    "username": "username_srtgb123",
                    "submitted_motion_$_ids": ["1"],
                    "submitted_motion_$1_ids": [34],
                },
                "meeting/1": {},
                "motion_submitter/34": {"user_id": 111, "motion_id": 50},
                "motion/50": {"submitter_ids": [34]},
            }
        )
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted(
            "user/111",
            {"submitted_motion_$1_ids": [34], "submitted_motion_$_ids": ["1"]},
        )
        self.assert_model_deleted(
            "motion_submitter/34", {"user_id": 111, "motion_id": 50}
        )
        self.assert_model_exists("motion/50", {"submitter_ids": []})

    def test_delete_with_template_field_set_null(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "active_meeting_ids": [1],
                    "enable_electronic_voting": True,
                },
                "meeting/1": {
                    "group_ids": [1],
                    "default_group_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "group/1": {
                    "meeting_id": 1,
                    "default_group_for_meeting_id": 1,
                    "user_ids": [2],
                },
                "user/2": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "poll_voted_$_ids": ["1"],
                    "poll_voted_$1_ids": [1],
                },
                "poll/1": {
                    "meeting_id": 1,
                    "voted_ids": [2],
                },
            }
        )
        response = self.request("user.delete", {"id": 2})
        self.assert_status_code(response, 200)

        self.assert_model_deleted("user/2")
        self.assert_model_exists("poll/1", {"voted_ids": []})
        self.assert_model_exists("group/1", {"user_ids": []})

    def test_delete_with_multiple_template_fields(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "active_meeting_ids": [1],
                    "enable_electronic_voting": True,
                },
                "meeting/1": {
                    "group_ids": [1],
                    "default_group_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "group/1": {
                    "meeting_id": 1,
                    "default_group_for_meeting_id": 1,
                    "user_ids": [2],
                },
                "user/2": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "poll_voted_$_ids": ["1"],
                    "poll_voted_$1_ids": [1],
                    "submitted_motion_$_ids": ["1"],
                    "submitted_motion_$1_ids": [1],
                },
                "poll/1": {
                    "meeting_id": 1,
                    "voted_ids": [2],
                },
                "motion_submitter/1": {
                    "user_id": 2,
                    "motion_id": 1,
                    "meeting_id": 1,
                },
                "motion/1": {
                    "meeting_id": 1,
                    "submitter_ids": [1],
                },
            }
        )
        response = self.request("user.delete", {"id": 2})
        self.assert_status_code(response, 200)

        self.assert_model_deleted("user/2")
        self.assert_model_exists("poll/1", {"voted_ids": []})
        self.assert_model_exists("group/1", {"user_ids": []})
        self.assert_model_deleted("motion_submitter/1")
        self.assert_model_exists("motion/1", {"submitter_ids": []})

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
