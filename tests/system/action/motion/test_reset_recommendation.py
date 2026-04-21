from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionResetRecommendationActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_motion(1, 22)
        self.set_models(
            {
                "motion_state/77": {
                    "meeting_id": 1,
                    "name": "test1",
                    "weight": 77,
                    "workflow_id": 1,
                },
            }
        )
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion/22": {"recommendation_id": 77}
        }

    def test_reset_recommendation_correct(self) -> None:
        check_time = datetime.now(ZoneInfo("UTC"))
        response = self.request("motion.reset_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.assert_model_exists("motion/22", {"recommendation_id": None})
        assert (
            model.get("last_modified", datetime.fromtimestamp(0, ZoneInfo("UTC")))
            >= check_time
        )
        self.assert_history_information("motion/22", ["Recommendation reset"])

    def test_reset_recommendation_correct_empty_recommendation(self) -> None:
        response = self.request("motion.reset_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/22", {"recommendation_id": None})

    def test_reset_recommendation_wrong(self) -> None:
        self.set_models(self.permission_test_models)
        response = self.request("motion.reset_recommendation", {"id": 21})
        self.assert_status_code(response, 400)
        self.assertEqual("Model 'motion/21' does not exist.", response.json["message"])
        self.assert_model_not_exists("motion/21")

    def test_reset_recommendation_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.reset_recommendation",
            {"id": 22},
        )

    def test_reset_recommendation_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.reset_recommendation",
            {"id": 22},
            Permissions.Motion.CAN_MANAGE_METADATA,
        )

    def test_reset_recommendation_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion.reset_recommendation",
            {"id": 22},
        )
