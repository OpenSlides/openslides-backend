from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionResetRecommendationActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)
        self.test_models: dict[str, dict[str, Any]] = {
            "motion_state/77": {
                "meeting_id": 222,
                "name": "test1",
                "weight": 77,
                "workflow_id": 222,
            },
        }
        self.permission_test_models: dict[str, dict[str, Any]] = {
            **self.test_models,
            "motion/22": {
                "meeting_id": 1,
                "title": "test1",
                "sequential_number": 22,
                "state_id": 1,
                "recommendation_id": 77,
            },
        }

    def set_test_models(self) -> None:
        self.create_motion(222, 22)
        self.set_models(self.test_models)

    def test_reset_recommendation_correct(self) -> None:
        check_time = datetime.now(ZoneInfo("UTC"))
        self.set_test_models()
        response = self.request("motion.reset_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("recommendation_id") is None
        assert (
            model.get("last_modified", datetime.fromtimestamp(0, ZoneInfo("UTC")))
            >= check_time
        )
        self.assert_history_information("motion/22", ["Recommendation reset"])

    def test_reset_recommendation_correct_empty_recommendation(self) -> None:
        self.set_models(
            {
                "motion_state/77": {
                    "meeting_id": 222,
                    "name": "test1",
                    "motion_recommendation_ids": [22],
                    "weight": 77,
                    "workflow_id": 222,
                },
                "motion/22": {
                    "meeting_id": 222,
                    "title": "test1",
                    "recommendation_id": None,
                    "sequential_number": 22,
                    "state_id": 222,
                },
            }
        )
        response = self.request("motion.reset_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("recommendation_id") is None

    def test_reset_recommendation_wrong(self) -> None:
        self.create_motion(222, 23)
        self.set_models(
            {
                "motion_state/77": {
                    "meeting_id": 222,
                    "name": "test1",
                    "weight": 77,
                    "workflow_id": 222,
                },
                "motion/23": {"recommendation_id": 77},
            }
        )
        response = self.request("motion.reset_recommendation", {"id": 22})
        self.assert_status_code(response, 400)
        self.assertEqual("Model 'motion/22' does not exist.", response.json["message"])
        self.assert_model_not_exists("motion/22")

    def test_reset_recommendation_no_permission(self) -> None:
        self.create_motion(222, 22)
        self.base_permission_test(
            self.permission_test_models,
            "motion.reset_recommendation",
            {"id": 22},
        )

    def test_reset_recommendation_permission(self) -> None:
        self.create_motion(222, 22)
        self.base_permission_test(
            self.permission_test_models,
            "motion.reset_recommendation",
            {"id": 22},
            Permissions.Motion.CAN_MANAGE_METADATA,
        )

    def test_reset_recommendation_permission_locked_meeting(self) -> None:
        self.create_motion(222, 22)
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion.reset_recommendation",
            {"id": 22},
        )
