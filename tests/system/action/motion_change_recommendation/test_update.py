from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionChangeRecommendationActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: Dict[str, Dict[str, Any]] = {
            "motion/25": {
                "title": "title_pheK0Ja3ai",
                "statute_paragraph_id": None,
                "meeting_id": 1,
            },
            "motion_change_recommendation/111": {
                "line_from": 11,
                "line_to": 23,
                "text": "text_LhmrbbwS",
                "motion_id": 25,
                "meeting_id": 1,
            },
        }

    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "motion/25": {
                    "title": "title_pheK0Ja3ai",
                    "statute_paragraph_id": None,
                    "meeting_id": 1,
                },
                "motion_change_recommendation/111": {
                    "line_from": 11,
                    "line_to": 23,
                    "text": "text_LhmrbbwS",
                    "motion_id": 25,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_change_recommendation.update",
            {
                "id": 111,
                "text": "text_zzTWoMte",
                "rejected": False,
                "internal": True,
                "type": "insertion",
                "other_description": "other_description_IClpabuM",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_change_recommendation/111")
        assert model.get("text") == "text_zzTWoMte"
        assert model.get("rejected") is False
        assert model.get("internal") is True
        assert model.get("type") == "insertion"
        assert model.get("other_description") == "other_description_IClpabuM"
        self.assert_history_information(
            "motion/25", ["Motion change recommendation updated"]
        )

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "motion/25": {
                    "title": "title_pheK0Ja3ai",
                    "statute_paragraph_id": None,
                    "meeting_id": 1,
                },
                "motion_change_recommendation/111": {
                    "line_from": 11,
                    "line_to": 23,
                    "text": "text_LhmrbbwS",
                    "motion_id": 25,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_change_recommendation.update", {"id": 112, "text": "text_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_change_recommendation/111")
        assert model.get("text") == "text_LhmrbbwS"
        assert model.get("line_from") == 11
        assert model.get("line_to") == 23
        assert model.get("motion_id") == 25

    def test_update_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_change_recommendation.update",
            {
                "id": 111,
                "text": "text_zzTWoMte",
            },
        )

    def test_update_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_change_recommendation.update",
            {
                "id": 111,
                "text": "text_zzTWoMte",
            },
            Permissions.Motion.CAN_MANAGE,
        )
