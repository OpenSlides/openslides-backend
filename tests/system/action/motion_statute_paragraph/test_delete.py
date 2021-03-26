from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionStatuteParagraphActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models(
            {"motion_statute_paragraph/111": {"meeting_id": 1}, "meeting/1": {}}
        )
        response = self.request("motion_statute_paragraph.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_statute_paragraph/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {"motion_statute_paragraph/112": {"meeting_id": 1}, "meeting/1": {}}
        )
        response = self.request("motion_statute_paragraph.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_statute_paragraph/112")

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            {"motion_statute_paragraph/111": {"meeting_id": 1}},
            "motion_statute_paragraph.delete",
            {"id": 111},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {"motion_statute_paragraph/111": {"meeting_id": 1}},
            "motion_statute_paragraph.delete",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )
