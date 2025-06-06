from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion/1": {"meeting_id": 1, "comment_ids": [111]},
            "motion_comment/111": {"meeting_id": 1, "section_id": 78, "motion_id": 1},
            "motion_comment_section/78": {
                "meeting_id": 1,
                "write_group_ids": [3],
                "name": "test",
            },
        }

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "user/1": {"meeting_user_ids": [1]},
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
                "meeting/1": {"admin_group_id": 2, "is_active_in_organization_id": 1},
                "group/2": {"meeting_id": 1, "admin_group_for_meeting_id": 1},
                "group/3": {"meeting_id": 1},
                "motion/1": {"meeting_id": 1, "comment_ids": [111]},
                "motion_comment/111": {
                    "meeting_id": 1,
                    "section_id": 78,
                    "motion_id": 1,
                },
                "motion_comment_section/78": {
                    "meeting_id": 1,
                    "write_group_ids": [3],
                    "name": "test",
                },
            }
        )
        response = self.request("motion_comment.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_comment/111")
        self.assert_history_information(
            "motion/1", ["Comment {} deleted", "motion_comment_section/78"]
        )

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion_comment/112")
        response = self.request("motion_comment.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_comment/112")

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_comment.delete",
            {"id": 111},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_comment.delete",
            {"id": 111},
            Permissions.Motion.CAN_SEE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion_comment.delete",
            {"id": 111},
        )

    def test_update_no_permission_cause_write_group(self) -> None:
        self.permission_test_models["motion_comment_section/78"]["write_group_ids"] = [
            2
        ]
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SEE])
        self.set_models(self.permission_test_models)
        response = self.request(
            "motion_comment.delete",
            {"id": 111},
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not in the write group of the section or in admin group."
            in response.json["message"]
        )

    def test_update_permission_cause_submitter(self) -> None:
        self.permission_test_models["motion_comment_section/78"]["write_group_ids"] = [
            2
        ]
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SEE])
        self.set_models(self.permission_test_models)
        self.set_models(
            {
                "motion/1": {"meeting_id": 1, "comment_ids": [111]},
                "motion_comment/111": {"motion_id": 1},
                "motion_submitter/12": {"meeting_user_id": 1, "motion_id": 1},
                "motion_comment_section/78": {"submitter_can_write": True},
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": self.user_id,
                    "motion_submitter_ids": [12],
                },
            }
        )

        response = self.request(
            "motion_comment.delete",
            {"id": 111},
        )
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_comment/111")
