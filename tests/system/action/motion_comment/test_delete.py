from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model: Dict[str, Dict[str, Any]] = {
            "motion_comment/111": {"meeting_id": 1, "section_id": 78},
            "motion_comment_section/78": {
                "meeting_id": 1,
                "write_group_ids": [3],
            },
        }

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "user/1": {"group_$1_ids": [2]},
                "meeting/1": {"admin_group_id": 2},
                "group/2": {"meeting_id": 1, "admin_group_for_meeting_id": 1},
                "group/3": {"meeting_id": 1},
                "motion_comment/111": {"meeting_id": 1, "section_id": 78},
                "motion_comment_section/78": {
                    "meeting_id": 1,
                    "write_group_ids": [3],
                },
            }
        )
        response = self.request("motion_comment.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_comment/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion_comment/112")
        response = self.request("motion_comment.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_comment/112")

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "motion_comment.delete",
            {"id": 111},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "motion_comment.delete",
            {"id": 111},
            Permissions.Motion.CAN_SEE,
        )

    def test_update_no_permission_cause_write_group(self) -> None:
        self.permission_test_model["motion_comment_section/78"]["write_group_ids"] = [2]
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SEE])
        self.set_models(self.permission_test_model)
        response = self.request(
            "motion_comment.delete",
            {"id": 111},
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not in the write group of the section or in admin group."
            in response.json["message"]
        )
