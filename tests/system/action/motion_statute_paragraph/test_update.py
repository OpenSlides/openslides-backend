from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionStatuteParagraphActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_statute_paragraph/111": {
                "title": "title_srtgb123",
                "meeting_id": 1,
            }
        }

    def test_update_correct(self) -> None:
        self.set_models(
            {
                "motion_statute_paragraph/111": {
                    "title": "title_srtgb123",
                    "meeting_id": 1,
                },
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request(
            "motion_statute_paragraph.update",
            {"id": 111, "title": "title_Xcdfgee", "text": "text_blablabla"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_statute_paragraph/111")
        model = self.get_model("motion_statute_paragraph/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("text") == "text_blablabla"

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "motion_statute_paragraph/111": {
                    "title": "title_srtgb123",
                    "meeting_id": 1,
                },
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request(
            "motion_statute_paragraph.update", {"id": 112, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_statute_paragraph/111")
        assert model.get("title") == "title_srtgb123"

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_statute_paragraph.update",
            {"id": 111, "title": "title_Xcdfgee", "text": "text_blablabla"},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_statute_paragraph.update",
            {"id": 111, "title": "title_Xcdfgee", "text": "text_blablabla"},
            Permissions.Motion.CAN_MANAGE,
        )
