from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_motion(1, 1)
        self.set_models(
            {
                "motion_comment/111": {
                    "meeting_id": 1,
                    "section_id": 78,
                    "motion_id": 1,
                },
                "motion_comment_section/78": {
                    "meeting_id": 1,
                    "name": "test",
                },
                "group/3": {"write_comment_section_ids": [78]},
            }
        )

    def test_delete_correct(self) -> None:
        self.set_user_groups(1, [2])
        response = self.request("motion_comment.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_comment/111")
        self.assert_history_information(
            "motion/1", ["Comment {} deleted", "motion_comment_section/78"]
        )

    def test_delete_wrong_id(self) -> None:
        self.set_user_groups(1, [2])
        response = self.request("motion_comment.delete", {"id": 112})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_comment/111")
        self.assertEqual(
            "Model 'motion_comment/112' does not exist.", response.json["message"]
        )

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test({}, "motion_comment.delete", {"id": 111})

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {}, "motion_comment.delete", {"id": 111}, Permissions.Motion.CAN_SEE
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_comment.delete", {"id": 111}
        )

    def test_update_no_permission_cause_write_group(self) -> None:
        self.user_id = self.create_user("user", [1])
        self.login(self.user_id)
        self.set_group_permissions(1, [Permissions.Motion.CAN_SEE])
        response = self.request("motion_comment.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertEqual(
            "You are not allowed to perform action motion_comment.delete. You are not in the write group of the section or in admin group.",
            response.json["message"],
        )

    def test_update_permission_cause_submitter(self) -> None:
        self.user_id = self.create_user("user", [1])
        self.login(self.user_id)
        self.set_group_permissions(1, [Permissions.Motion.CAN_SEE])
        self.set_models(
            {
                "motion_submitter/12": {
                    "meeting_id": 1,
                    "meeting_user_id": 1,
                    "motion_id": 1,
                },
                "motion_comment_section/78": {"submitter_can_write": True},
            }
        )

        response = self.request("motion_comment.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_comment/111")
