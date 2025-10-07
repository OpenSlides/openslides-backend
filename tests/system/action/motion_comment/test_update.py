from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_motion(1, 111)
        self.set_models(
            {
                "motion_comment/111": {
                    "comment": "comment_srtgb123",
                    "meeting_id": 1,
                    "motion_id": 111,
                    "section_id": 78,
                },
                "motion_comment_section/78": {
                    "meeting_id": 1,
                    "name": "test",
                },
                "group/3": {"write_comment_section_ids": [78]},
            }
        )

    def test_update_correct(self) -> None:
        self.set_user_groups(1, [2])
        response = self.request(
            "motion_comment.update", {"id": 111, "comment": "comment_Xcdfgee"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_comment/111", {"comment": "comment_Xcdfgee"})
        self.assert_history_information(
            "motion/111", ["Comment {} updated", "motion_comment_section/78"]
        )

    def test_update_wrong_id(self) -> None:
        response = self.request(
            "motion_comment.update", {"id": 112, "comment": "comment_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_comment/111", {"comment": "comment_srtgb123"})

    def test_update_no_permission(self) -> None:
        self.base_permission_test(
            {}, "motion_comment.update", {"id": 111, "comment": "comment_Xcdfgee"}
        )

    def test_update_permission(self) -> None:
        self.user_id = self.create_user("user", [3])
        self.login(self.user_id)
        self.set_group_permissions(3, [Permissions.Motion.CAN_SEE])
        response = self.request(
            "motion_comment.update",
            {"comment": "test_Xcdfgee", "id": 111},
        )
        self.assert_status_code(response, 200)

    def test_update_no_permission_cause_write_group(self) -> None:
        self.user_id = self.create_user("user", [1])
        self.login(self.user_id)
        self.set_group_permissions(1, [Permissions.Motion.CAN_SEE])
        response = self.request(
            "motion_comment.update",
            {"comment": "test_Xcdfgee", "id": 111},
        )
        self.assert_status_code(response, 403)
        self.assertEqual(
            "You are not allowed to perform action motion_comment.update. You are not in the write group of the section or in admin group.",
            response.json["message"],
        )

    def test_update_permission_in_admin_group(self) -> None:
        self.user_id = self.create_user("user")
        self.set_user_groups(self.user_id, [2])
        self.login(self.user_id)
        response = self.request(
            "motion_comment.update",
            {"comment": "test_Xcdfgee", "id": 111},
        )
        self.assert_status_code(response, 200)

    def test_update_permission_cause_submitter(self) -> None:
        self.user_id = self.create_user("user", [1])
        self.login(self.user_id)
        self.set_group_permissions(1, [Permissions.Motion.CAN_SEE])
        self.set_models(
            {
                "motion_comment_section/78": {"submitter_can_write": True},
                "motion_submitter/777": {
                    "meeting_id": 1,
                    "meeting_user_id": 1,
                    "motion_id": 111,
                },
            }
        )
        response = self.request(
            "motion_comment.update",
            {"comment": "test_Xcdfgee", "id": 111},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_comment/111", {"comment": "test_Xcdfgee"})
