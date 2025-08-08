from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSetRecommendationActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)
        self.create_motion(222, 22)
        self.test_models = {
            "motion_state/77": {
                "name": "recommendation",
                "meeting_id": 222,
                "workflow_id": 22,
                "weight": 77,
                "recommendation_label": "blablabal",
            }
        }
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_workflow/34": {
                "meeting_id": 1,
                "name": "Workflow 34",
                "sequential_number": 1,
                "first_state_id": 66,
            },
            "motion_state/66": {
                "name": "Default state 66",
                "meeting_id": 1,
                "motion_ids": [22],
                "workflow_id": 34,
                "weight": 66,
            },
            "motion_state/77": {
                "name": "recommendation",
                "meeting_id": 1,
                "workflow_id": 34,
                "weight": 77,
                "recommendation_label": "blablabal",
            },
            "motion/22": {
                "title": "Motion 22",
                "meeting_id": 1,
                "state_id": 66,
            },
        }

    def test_set_recommendation_correct(self) -> None:
        check_time = datetime.now(ZoneInfo("UTC"))
        self.set_models(self.test_models)
        response = self.request(
            "motion.set_recommendation", {"id": 22, "recommendation_id": 77}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("recommendation_id") == 77
        assert model.get("last_modified", 0) >= check_time
        self.assert_history_information(
            "motion/22", ["Recommendation set to {}", "motion_state/77"]
        )

    def test_set_recommendation_not_matching_workflow_ids(self) -> None:
        self.create_motion(222, 123)
        self.set_models(
            {
                "motion_state/77": {
                    "name": "Motion with wrong workflow",
                    "meeting_id": 222,
                    "workflow_id": 123,
                    "weight": 123,
                    "recommendation_label": "blablabal",
                },
            }
        )
        response = self.request(
            "motion.set_recommendation", {"id": 22, "recommendation_id": 77}
        )
        self.assert_status_code(response, 400)
        assert "State is from a different workflow as motion." in response.json.get(
            "message", ""
        )

    def test_history_multiple_actions(self) -> None:
        self.set_models(
            {
                **self.test_models,
                "motion/23": {
                    "title": "motion23",
                    "sequential_number": 23,
                    "state_id": 22,
                    "meeting_id": 222,
                },
            }
        )
        response = self.request_multi(
            "motion.set_recommendation",
            [{"id": 22, "recommendation_id": 77}, {"id": 23, "recommendation_id": 77}],
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            "motion/22", ["Recommendation set to {}", "motion_state/77"]
        )
        self.assert_history_information(
            "motion/23", ["Recommendation set to {}", "motion_state/77"]
        )

    def test_history_multiple_actions_different_states(self) -> None:
        self.create_motion(222, 23)
        self.set_models(
            {
                **self.test_models,
                "motion_state/66": {
                    "name": "recommendation2",
                    "meeting_id": 222,
                    "workflow_id": 23,
                    "weight": 66,
                    "recommendation_label": "blablabal",
                },
            }
        )
        response = self.request_multi(
            "motion.set_recommendation",
            [{"id": 22, "recommendation_id": 77}, {"id": 23, "recommendation_id": 66}],
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            "motion/22", ["Recommendation set to {}", "motion_state/77"]
        )
        self.assert_history_information(
            "motion/23", ["Recommendation set to {}", "motion_state/66"]
        )

    def test_set_recommendation_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.set_recommendation",
            {"id": 22, "recommendation_id": 77},
        )

    def test_set_recommendation_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.set_recommendation",
            {"id": 22, "recommendation_id": 77},
            Permissions.Motion.CAN_MANAGE_METADATA,
        )

    def test_set_recommendation_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion.set_recommendation",
            {"id": 22, "recommendation_id": 77},
        )
