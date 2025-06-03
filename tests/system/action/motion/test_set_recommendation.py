import time
from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSetRecommendationActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_workflow/34": {
                "meeting_id": 1,
            },
            "motion_state/66": {
                "meeting_id": 1,
                "motion_ids": [22],
                "workflow_id": 34,
            },
            "motion_state/77": {
                "meeting_id": 1,
                "workflow_id": 34,
                "recommendation_label": "blablabal",
            },
            "motion/22": {"meeting_id": 1, "state_id": 66},
        }

    def test_set_recommendation_correct(self) -> None:
        check_time = round(time.time())
        self.set_models(
            {
                "motion_workflow/34": {
                    "meeting_id": 222,
                },
                "motion_state/66": {
                    "meeting_id": 222,
                    "motion_ids": [22],
                    "workflow_id": 34,
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "workflow_id": 34,
                    "recommendation_label": "blablabal",
                },
                "motion/22": {"meeting_id": 222, "state_id": 66},
            }
        )
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

    def test_set_recommendation_missing_recommendation_label(self) -> None:
        self.set_models(
            {
                "motion_workflow/34": {
                    "meeting_id": 222,
                },
                "motion_state/66": {
                    "meeting_id": 222,
                    "motion_ids": [22],
                    "workflow_id": 34,
                },
                "motion_state/77": {"meeting_id": 222, "workflow_id": 34},
                "motion/22": {"meeting_id": 222, "state_id": 66},
            }
        )
        response = self.request(
            "motion.set_recommendation", {"id": 22, "recommendation_id": 77}
        )
        self.assert_status_code(response, 400)
        assert "Recommendation label of a recommendation must be set." in str(
            response.json["message"]
        )

    def test_set_recommendation_not_matching_workflow_ids(self) -> None:
        self.set_models(
            {
                "motion_workflow/34": {
                    "meeting_id": 222,
                },
                "motion_state/66": {
                    "meeting_id": 222,
                    "motion_ids": [22],
                    "workflow_id": 34,
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "workflow_id": 123,
                    "recommendation_label": "blablabal",
                },
                "motion/22": {"meeting_id": 222, "state_id": 66},
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
                "motion_workflow/34": {
                    "meeting_id": 222,
                },
                "motion_state/66": {
                    "meeting_id": 222,
                    "motion_ids": [22],
                    "workflow_id": 34,
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "workflow_id": 34,
                    "recommendation_label": "blablabal",
                },
                "motion/22": {"meeting_id": 222, "state_id": 66},
                "motion/23": {"meeting_id": 222, "state_id": 66},
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
        self.set_models(
            {
                "motion_workflow/34": {
                    "meeting_id": 222,
                },
                "motion_state/66": {
                    "meeting_id": 222,
                    "motion_ids": [22],
                    "workflow_id": 34,
                    "recommendation_label": "blablabal",
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "motion_ids": [23],
                    "workflow_id": 34,
                    "recommendation_label": "blablabal",
                },
                "motion/22": {"meeting_id": 222, "state_id": 66},
                "motion/23": {"meeting_id": 222, "state_id": 77},
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
