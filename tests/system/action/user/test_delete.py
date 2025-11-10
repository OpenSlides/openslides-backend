from datetime import datetime
from zoneinfo import ZoneInfo

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase
from openslides_backend.models.models import Poll
from .scope_permissions_mixin import ScopePermissionsTestMixin, UserScope


class UserDeleteActionTest(ScopePermissionsTestMixin, BaseActionTestCase):
    permission = Permissions.User.CAN_MANAGE

    def test_delete_correct(self) -> None:
        self.create_model("user/111", {"username": "username_srtgb123"})
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")
        self.assert_history_information("user/111", ["Account deleted"])

    def test_delete_wrong_id(self) -> None:
        self.create_model("user/112", {"username": "username_srtgb123"})
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 400)
        model = self.get_model("user/112")
        assert model.get("username") == "username_srtgb123"

    def test_delete_correct_with_groups_and_locked_meeting(self) -> None:
        self.create_meeting(42)
        self.set_models(
            {
                "user/111": {
                    "username": "username_srtgb123",
                },
                "meeting_user/1111": {
                    "meeting_id": 42,
                    "user_id": 111,
                    "group_ids": [456],
                },
                "group/456": {
                    "name": "shroup",
                    "meeting_id": 42,
                    "meeting_user_ids": [1111],
                },
                "meeting/42": {
                    "locked_from_inside": True,
                },
                "committee/101": {
                    "manager_ids": [111],
                },
            }
        )
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")
        self.assert_model_not_exists("meeting_user/1111")
        self.assert_model_exists("group/456", {"user_ids": None})
        self.assert_history_information(
            "user/111",
            ["Participant removed from meeting {}", "meeting/42", "Account deleted"],
        )

    def test_delete_with_speaker(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/111": {
                    "username": "username_srtgb123",
                    "meeting_user_ids": [1111],
                    "is_present_in_meeting_ids": [1],
                },
                "meeting_user/1111": {
                    "meeting_id": 1,
                    "user_id": 111,
                    "speaker_ids": [15, 16],
                },
                "speaker/15": {
                    # "begin_time": 12345678,
                    "begin_time": datetime(2012, 5, 31, 0, 0, tzinfo=ZoneInfo("UTC")),
                    "list_of_speakers_id": 1,
                    "meeting_user_id": 1111,
                    "meeting_id": 1,
                },
                "speaker/16": {
                    "list_of_speakers_id": 1,
                    "meeting_user_id": 1111,
                    "meeting_id": 1,
                },
                "list_of_speakers/1": {
                    "sequential_number": 1,
                    "meeting_id": 1,
                    "content_object_id": "topic/1",
                },
                "topic/1": {
                    "title": "tropic",
                    "sequential_number": 1,
                    "meeting_id": 1,
                },
                "agenda_item/8": {"meeting_id": 1, "content_object_id": "topic/1"},
            }
        )
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")
        self.assert_model_not_exists("meeting_user/1111")
        self.assert_model_exists(
            "speaker/15",
            {
                "meeting_user_id": None,
                "meeting_id": 1,
                "begin_time": datetime(2012, 5, 31, 0, 0, tzinfo=ZoneInfo("UTC")),
            },
        )
        self.assert_model_not_exists("speaker/16")
        self.assert_model_exists("meeting/1", {"present_user_ids": None})

    def test_delete_with_candidate(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/111": {
                    "username": "username_srtgb123",
                    "meeting_user_ids": [1111],
                },
                "meeting_user/1111": {
                    "meeting_id": 1,
                    "user_id": 111,
                    "assignment_candidate_ids": [34],
                },
                "meeting/1": {"meeting_user_ids": [1111]},
                "assignment_candidate/34": {
                    "meeting_user_id": 1111,
                    "meeting_id": 1,
                    "assignment_id": 123,
                },
                "assignment/123": {
                    "title": "test_assignment",
                    "candidate_ids": [34],
                    "sequential_number": 123,
                    "meeting_id": 1,
                },
                "list_of_speakers/23": {
                    "content_object_id": "assignment/123",
                    "sequential_number": 11,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")
        self.assert_model_not_exists("meeting_user/1111")
        self.assert_model_exists(
            "assignment_candidate/34", {"assignment_id": 123, "meeting_user_id": None}
        )
        self.assert_model_exists("assignment/123", {"candidate_ids": [34]})

    def test_delete_with_submitter(self) -> None:
        self.create_meeting()
        self.create_motion(1, 50)
        self.set_models(
            {
                "user/111": {
                    "username": "username_srtgb123",
                    "meeting_user_ids": [1111],
                },
                "motion_submitter/34": {
                    "meeting_user_id": 1111,
                    "motion_id": 50,
                    "meeting_id": 1,
                },
                "meeting_user/1111": {
                    "meeting_id": 1,
                    "user_id": 111,
                    "motion_submitter_ids": [34],
                },
                "motion/50": {"submitter_ids": [34]},
            }
        )
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")
        self.assert_model_not_exists("meeting_user/1111")
        self.assert_model_not_exists("motion_submitter/34")
        self.assert_model_exists("motion/50", {"submitter_ids": None})

    def test_delete_with_poll_candidate(self) -> None:
        self.create_meeting()
        user_id = self.create_user_for_meeting(1)
        self.set_models(
            {
                "poll/1": {
                    "title": "Poll 1",
                    "meeting_id": 1,
                    "content_object_id": "assignment/1",
                    "visibility": Poll.VISIBILITY_NAMED,
                    "config_id": "poll_config_approval/1",
                    "state": Poll.STATE_FINISHED,
                },
                "list_of_speakers/1": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/1",
                },
                "assignment/1": {
                    "id": 1,
                    "title": "Duckburg town council",
                    "meeting_id": 1,
                },
                "poll_config_option/1": {
                    "poll_config_id": "poll_config_approval/1",
                    "meeting_user_id": 1,
                },
                "poll_config_approval/1": {"poll_id": 1},
            }
        )
        response = self.request("user.delete", {"id": user_id})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists(f"user/{user_id}")
        self.assert_model_not_exists("meeting_user/1")
        self.assert_model_exists("poll_config_option/1", {"meeting_user_id": None})

    def test_delete_with_group_ids_set_null(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "active_meeting_ids": [1],
                    "enable_electronic_voting": True,
                },
                "meeting/1": {"name": "meaty"},
                "group/1": {
                    "default_group_for_meeting_id": 1,
                    "meeting_user_ids": [12],
                },
                "user/2": {
                    "meeting_user_ids": [12],
                    "username": "somebody",
                },
                "meeting_user/12": {
                    "meeting_id": 1,
                    "user_id": 2,
                    "group_ids": [1],
                },
            }
        )
        response = self.request("user.delete", {"id": 2})
        self.assert_status_code(response, 200)

        self.assert_model_not_exists("user/2")
        self.assert_model_exists("group/1", {"meeting_user_ids": None})

    def test_delete_with_multiple_fields(self) -> None:
        self.create_meeting()
        self.create_motion(1)
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "active_meeting_ids": [1],
                    "enable_electronic_voting": True,
                },
                "meeting/1": {
                    "meeting_user_ids": [12],
                },
                "user/2": {
                    "username": "somebody",
                    "meeting_user_ids": [12],
                },
                "meeting_user/12": {
                    "meeting_id": 1,
                    "user_id": 2,
                    "motion_submitter_ids": [1],
                    "group_ids": [1],
                },
                "motion_submitter/1": {
                    "meeting_user_id": 12,
                    "motion_id": 1,
                    "meeting_id": 1,
                },
                "motion/1": {"submitter_ids": [1]},
            }
        )
        response = self.request("user.delete", {"id": 2})
        self.assert_status_code(response, 200)

        self.assert_model_not_exists("user/2")
        self.assert_model_not_exists("meeting_user/12")
        self.assert_model_exists("group/1", {"meeting_user_ids": None})
        self.assert_model_not_exists("motion_submitter/1")
        self.assert_model_exists("motion/1", {"submitter_ids": None})

    def test_delete_with_delegation_to(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/111": {
                    "username": "u111",
                    "meeting_user_ids": [1111],
                },
                "user/112": {
                    "username": "u112",
                    "meeting_user_ids": [1112],
                },
                "meeting_user/1111": {
                    "meeting_id": 1,
                    "user_id": 111,
                    "vote_delegated_to_id": 1112,
                },
                "meeting_user/1112": {
                    "meeting_id": 1,
                    "user_id": 112,
                    "vote_delegations_from_ids": [1111],
                },
                "meeting/1": {"meeting_user_ids": [1111, 1112]},
            }
        )
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")
        self.assert_model_not_exists("meeting_user/1111")
        self.assert_model_exists("user/112")
        self.assert_model_exists("meeting_user/1112")

    def test_delete_with_delegation_from(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/111": {
                    "username": "u111",
                    "meeting_user_ids": [1111],
                },
                "user/112": {
                    "username": "u112",
                    "meeting_user_ids": [1112],
                },
                "meeting_user/1111": {
                    "meeting_id": 1,
                    "user_id": 111,
                    "vote_delegated_to_id": 1112,
                },
                "meeting_user/1112": {
                    "meeting_id": 1,
                    "user_id": 112,
                    "vote_delegations_from_ids": [1111],
                },
                "meeting/1": {"meeting_user_ids": [1111, 1112]},
            }
        )
        response = self.request("user.delete", {"id": 112})

        self.assert_status_code(response, 200)
        self.assert_model_exists("user/111", {"meeting_user_ids": [1111]})
        self.assert_model_not_exists("user/112")
        self.assert_model_exists("meeting_user/1111")
        self.assert_model_not_exists("meeting_user/1112")

    def test_delete_scope_meeting_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 60 or Permission user.can_manage in meeting 1",
            response.json["message"],
        )

    def test_delete_scope_meeting_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")

    def test_delete_scope_meeting_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")

    def test_delete_scope_meeting_permission_in_meeting_can_update(self) -> None:
        self.setup_admin_scope_permissions(
            UserScope.Meeting, Permissions.User.CAN_UPDATE
        )
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 60 or Permission user.can_manage in meeting 1",
            response.json["message"],
        )

    def test_delete_scope_meeting_permission_in_meeting_can_manage(self) -> None:
        self.setup_admin_scope_permissions(
            UserScope.Meeting, Permissions.User.CAN_MANAGE
        )
        self.setup_scoped_user(UserScope.Meeting)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")

    def test_delete_scope_committee_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 60",
            response.json["message"],
        )

    def test_delete_scope_committee_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")

    def test_delete_scope_committee_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Committee)
        self.assert_model_exists("user/111")
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")

    def test_delete_scope_committee_permission_in_meeting(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Meeting)
        self.setup_scoped_user(UserScope.Committee)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 60",
            response.json["message"],
        )

    def test_delete_scope_organization_no_permission(self) -> None:
        self.setup_admin_scope_permissions(None)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 4",
            response.json["message"],
        )

    def test_delete_scope_organization_permission_in_organization(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")

    def test_delete_scope_organization_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.set_models(
            {
                "user/111": {
                    "username": "somebody",
                },
                "group/11": {"name": "soup", "meeting_id": 1},
                "group/22": {"name": "troup", "meeting_id": 4},
            }
        )
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
            response.json["message"],
        )

    def test_delete_scope_multi_committee_permission_in_committee(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Committee)
        self.setup_scoped_user(UserScope.Organization)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")

    def test_delete_scope_organization_permission_in_one_meeting_one_shared_meeting(
        self,
    ) -> None:
        self.setup_two_meetings_in_different_committees()
        self.set_user_groups(1, [2])
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 4",
            response.json["message"],
        )

    def test_delete_scope_organization_permission_in_one_meeting_two_shared_meetings(
        self,
    ) -> None:
        self.setup_two_meetings_in_different_committees()
        self.set_user_groups(1, [2, 4])
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 4",
            response.json["message"],
        )

    def test_delete_scope_organization_permission_in_all_meetings(self) -> None:
        self.setup_scope_organization_with_permission_in_all_meetings(self.permission)
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/111")

    def test_delete_scope_organization_permission_in_meeting_archived_meetings_in_different_committees(
        self,
    ) -> None:
        self.setup_archived_meetings_in_different_committees()
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committees {60, 63}",
            response.json["message"],
        )

    def test_delete_superadmin_with_1_meeting_by_oml_usermanager(self) -> None:
        self.setup_admin_scope_permissions(UserScope.Organization)
        self.setup_scoped_user(UserScope.Meeting)
        self.set_models(
            {
                "user/111": {
                    "organization_management_level": OrganizationManagementLevel.SUPERADMIN
                }
            }
        )
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permission: OrganizationManagementLevel superadmin in organization 1",
            response.json["message"],
        )

    def test_delete_prevent_delete_oneself(self) -> None:
        response = self.request("user.delete", {"id": 1})
        self.assert_status_code(response, 400)
        assert "You cannot delete yourself." in response.json["message"]

    def test_delete_last_meeting_admin(self) -> None:
        self.create_meeting()
        self.create_user("username_srtgb123", [2])
        response = self.request("user.delete", {"id": 2})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot remove last admin from meeting(s) 1",
            response.json["message"],
        )

    def test_delete_non_last_meeting_admin(self) -> None:
        self.create_meeting()
        self.create_user("username_srtgb123", [2])
        self.create_user("username_srtgb456", [2])
        response = self.request("user.delete", {"id": 2})
        self.assert_status_code(response, 200)

    def test_delete_both_meeting_admins(self) -> None:
        self.create_meeting()
        self.create_user("username_srtgb123", [2])
        self.create_user("username_srtgb456", [2])
        response = self.request_multi("user.delete", [{"id": 2}, {"id": 3}])
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot remove last admin from meeting(s) 1",
            response.json["message"],
        )

    def test_delete_last_meeting_admin_of_template_meeting(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"template_for_organization_id": 1},
                "organization/1": {"template_meeting_ids": [1]},
            }
        )
        self.create_user("username_srtgb123", [2])
        response = self.request("user.delete", {"id": 2})
        self.assert_status_code(response, 200)

    def test_delete_non_last_meeting_admin_from_two_meetings(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.create_user("username_srtgb123", [2, 5])
        response = self.request("user.delete", {"id": 2})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot remove last admin from meeting(s) 1, 4",
            response.json["message"],
        )
