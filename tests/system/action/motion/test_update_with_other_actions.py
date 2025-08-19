from tests.system.action.base import BaseActionTestCase


class MotionUpdateWithOtherActionsTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)
        self.create_motion(222, 22)
        self.set_models(
            {
                "motion_state/222": {"next_state_ids": [77]},
                "motion_state/77": {
                    "name": "test",
                    "weight": 77,
                    "meeting_id": 222,
                    "workflow_id": 222,
                    "recommendation_label": "label",
                },
                "motion_category/3": {
                    "meeting_id": 222,
                    "name": "category",
                    "sequential_number": 3,
                },
            }
        )

    def test_update_with_set_recommendation(self) -> None:
        response = self.request_json(
            [
                {"action": "motion.update", "data": [{"id": 22, "category_id": 3}]},
                {
                    "action": "motion.set_recommendation",
                    "data": [{"id": 22, "recommendation_id": 77}],
                },
            ]
        )
        self.assert_status_code(response, 200)

    def test_update_with_set_state(self) -> None:
        response = self.request_json(
            [
                {"action": "motion.update", "data": [{"id": 22, "category_id": 3}]},
                {"action": "motion.set_state", "data": [{"id": 22, "state_id": 77}]},
            ]
        )
        self.assert_status_code(response, 200)
