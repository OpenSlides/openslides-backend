from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_motion(1, 357)
        self.set_models(
            {
                "motion_comment_section/78": {
                    "meeting_id": 1,
                    "name": "test",
                },
                "group/3": {"write_comment_section_ids": [78]},
            }
        )

    def test_create(self) -> None:
        self.set_user_groups(1, [3])
        response = self.request(
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_comment/1",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_history_information(
            "motion/357", ["Comment {} created", "motion_comment_section/78"]
        )

    def test_create_not_unique_error(self) -> None:
        self.set_user_groups(1, [2])
        self.set_models(
            {
                "motion_comment/4356": {
                    "comment": "test_Xcdfgee",
                    "motion_id": 357,
                    "section_id": 78,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "There already exists a comment for this section, please update it instead.",
            response.json["message"],
        )

    def test_create_empty_data(self) -> None:
        response = self.request("motion_comment.create", {})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action motion_comment.create: data must contain ['comment', 'motion_id', 'section_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "motion_comment.create",
            {
                "comment": "test_Xcdfgee",
                "motion_id": 357,
                "section_id": 78,
                "wrong_field": "text_AefohteiF8",
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action motion_comment.create: data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_no_permission(self) -> None:
        self.base_permission_test(
            {},
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )

    def test_create_permission(self) -> None:
        self.base_permission_test(
            {},
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
            Permissions.Motion.CAN_SEE,
        )

    def test_create_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )

    def test_create_no_permission_cause_write_group(self) -> None:
        self.user_id = self.create_user("user", [1])
        self.login(self.user_id)
        self.set_group_permissions(1, [Permissions.Motion.CAN_SEE])
        response = self.request(
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_status_code(response, 403)
        self.assertEqual(
            "You are not allowed to perform action motion_comment.create. You are not in the write group of the section or in admin group.",
            response.json["message"],
        )

    def test_create_permission_cause_submitter(self) -> None:
        self.user_id = self.create_user("user", [1])
        self.login(self.user_id)
        self.set_group_permissions(1, [Permissions.Motion.CAN_SEE])
        self.set_models(
            {
                "motion_comment_section/78": {"submitter_can_write": True},
                "motion_submitter/1234": {
                    "meeting_user_id": 1,
                    "motion_id": 357,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_comment/1",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "group_ids": [1],
                "motion_submitter_ids": [1234],
                "meeting_id": 1,
                "user_id": 2,
            },
        )

    def test_create_permission_non_meeting_committee_admin(self) -> None:
        self.set_committee_management_level([60])
        self.base_create_permission_non_meeting_admin()

    def test_create_permission_non_meeting_parent_committee_admin(self) -> None:
        self.create_committee(59)
        self.set_committee_management_level([59])
        self.set_models(
            {
                "committee/59": {"child_ids": [60], "all_child_ids": [60]},
                "committee/60": {"parent_id": 59, "all_parent_ids": [59]},
            }
        )
        self.base_create_permission_non_meeting_admin()

    def test_create_permission_non_meeting_orga_admin(self) -> None:
        self.base_create_permission_non_meeting_admin(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )

    def test_create_permission_non_meeting_superadmin(self) -> None:
        self.base_create_permission_non_meeting_admin(
            OrganizationManagementLevel.SUPERADMIN
        )

    def base_create_permission_non_meeting_admin(
        self, permission: OrganizationManagementLevel | None = None
    ) -> None:
        self.set_organization_management_level(permission)
        response = self.request(
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_comment/1", {"comment": "test_Xcdfgee"})
