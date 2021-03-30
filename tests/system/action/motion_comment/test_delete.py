from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model = {
            "motion_comment/111": {"meeting_id": 1, "section_id": 78},
            "motion_comment_section/78": {
                "meeting_id": 1,
                "write_group_ids": [3],
            },
        }

    def test_delete_correct(self) -> None:
        self.set_models({"meeting/1": {}, "motion_comment/111": {"meeting_id": 1}})
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
