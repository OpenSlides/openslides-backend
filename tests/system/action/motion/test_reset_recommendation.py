import time
from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionResetRecommendationActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_state/77": {
                "meeting_id": 1,
                "name": "test1",
                "motion_recommendation_ids": [22],
            },
            "motion/22": {
                "meeting_id": 1,
                "title": "test1",
                "recommendation_id": 77,
            },
        }

    def test_reset_recommendation_correct(self) -> None:
        check_time = round(time.time())
        self.set_models(
            {
                "committee/1": {"meeting_ids": [222]},
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                    "committee_id": 1
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "name": "test1",
                    "motion_recommendation_ids": [22],
                },
                "motion/22": {
                    "meeting_id": 222,
                    "title": "test1",
                    "recommendation_id": 77,
                },
            }
        )
        response = self.request("motion.reset_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("recommendation_id") is None
        assert model.get("last_modified", 0) >= check_time
        self.assert_history_information("motion/22", ["Recommendation reset"])

    def test_reset_recommendation_correct_empty_recommendation(self) -> None:
        self.set_models(
            {
                "committee/1": {"meeting_ids": [222]},
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                    "committee_id": 1
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "name": "test1",
                    "motion_recommendation_ids": [22],
                },
                "motion/22": {
                    "meeting_id": 222,
                    "title": "test1",
                    "recommendation_id": None,
                },
            }
        )
        response = self.request("motion.reset_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("recommendation_id") is None

    def test_reset_recommendation_wrong(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_SNLGsvIV"},
                "motion_state/77": {
                    "meeting_id": 222,
                    "name": "test1",
                    "motion_recommendation_ids": [22],
                },
                "motion/23": {
                    "meeting_id": 222,
                    "title": "test1",
                    "recommendation_id": 77,
                },
            }
        )
        response = self.request("motion.reset_recommendation", {"id": 22})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("motion/22")

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
