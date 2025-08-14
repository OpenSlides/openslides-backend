from tests.system.action.base import BaseActionTestCase


class MotionChangeRecommendationActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "motion/1": {
                    "title": "motion 1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "sequential_number": 1,
                },
                "motion_change_recommendation/111": {"meeting_id": 1, "motion_id": 1},
            }
        )

    def test_delete_correct(self) -> None:
        response = self.request("motion_change_recommendation.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_change_recommendation/111")
        self.assert_history_information(
            "motion/1", ["Motion change recommendation deleted"]
        )

    def test_delete_wrong_id(self) -> None:
        response = self.request("motion_change_recommendation.delete", {"id": 112})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Model 'motion_change_recommendation/112' does not exist.",
            response.json["message"],
        )
        self.assert_model_exists("motion_change_recommendation/111")

    def test_delete_no_permission(self) -> None:
        self.base_permission_test(
            {}, "motion_change_recommendation.delete", {"id": 111}
        )

    def test_delete_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_change_recommendation.delete", {"id": 111}
        )
