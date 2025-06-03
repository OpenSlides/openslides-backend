from tests.system.action.base import BaseActionTestCase


class MotionUpdateWithOtherActionsTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)
        self.set_models(
            {
                "motion_workflow/34": {
                    "meeting_id": 222,
                },
                "motion_state/66": {
                    "meeting_id": 222,
                    "motion_ids": [22],
                    "workflow_id": 34,
                    "next_state_ids": [77],
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "workflow_id": 34,
                    "recommendation_label": "label",
                    "name": "test",
                },
                "motion_category/3": {
                    "meeting_id": 222,
                    "name": "category",
                },
                "motion/22": {"meeting_id": 222, "state_id": 66},
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
