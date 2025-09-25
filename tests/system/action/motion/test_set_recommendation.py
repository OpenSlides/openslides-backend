from datetime import datetime
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSetRecommendationActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_motion(1, 22)
        self.set_models(
            {
                "motion_state/77": {
                    "name": "recommendation",
                    "meeting_id": 1,
                    "workflow_id": 1,
                    "weight": 77,
                    "recommendation_label": "blablabal",
                }
            }
        )

    def test_set_recommendation_correct(self) -> None:
        check_time = datetime.now(ZoneInfo("UTC"))
        response = self.request(
            "motion.set_recommendation", {"id": 22, "recommendation_id": 77}
        )
        self.assert_status_code(response, 200)
        model = self.assert_model_exists("motion/22", {"recommendation_id": 77})
        assert (
            model.get("last_modified", datetime.fromtimestamp(0, ZoneInfo("UTC")))
            >= check_time
        )
        self.assert_history_information(
            "motion/22", ["Recommendation set to {}", "motion_state/77"]
        )

    def test_set_recommendation_missing_recommendation_label(self) -> None:
        self.set_models({"motion_state/77": {"recommendation_label": None}})
        response = self.request(
            "motion.set_recommendation", {"id": 22, "recommendation_id": 77}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Recommendation label of a recommendation must be set.",
            response.json["message"],
        )

    def test_set_recommendation_not_matching_workflow_ids(self) -> None:
        self.set_models(
            {
                "motion_workflow/2": {
                    "name": "motion_workflow 2",
                    "sequential_number": 2,
                    "first_state_id": 77,
                    "meeting_id": 1,
                },
                "motion_state/77": {"workflow_id": 2},
            }
        )
        response = self.request(
            "motion.set_recommendation", {"id": 22, "recommendation_id": 77}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Cannot set recommendation. State is from a different workflow as motion.",
            response.json["message"],
        )

    def test_history_multiple_actions(self) -> None:
        self.create_motion(1, 23)
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
        self.create_motion(1, 23)
        self.set_models(
            {
                "motion_state/66": {
                    "name": "recommendation2",
                    "meeting_id": 1,
                    "workflow_id": 1,
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
            {}, "motion.set_recommendation", {"id": 22, "recommendation_id": 77}
        )

    def test_set_recommendation_permission(self) -> None:
        self.base_permission_test(
            {},
            "motion.set_recommendation",
            {"id": 22, "recommendation_id": 77},
            Permissions.Motion.CAN_MANAGE_METADATA,
        )

    def test_set_recommendation_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion.set_recommendation", {"id": 22, "recommendation_id": 77}
        )
