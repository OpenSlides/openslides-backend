from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionStatuteParagraphActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_statute_paragraph/111": {"meeting_id": 1}
        }

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "motion_statute_paragraph/111": {"meeting_id": 1},
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request("motion_statute_paragraph.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_statute_paragraph/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "motion_statute_paragraph/112": {"meeting_id": 1},
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request("motion_statute_paragraph.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_statute_paragraph/112")

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_statute_paragraph.delete",
            {"id": 111},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_statute_paragraph.delete",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )
