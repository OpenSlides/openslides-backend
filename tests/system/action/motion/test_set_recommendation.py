from tests.system.action.base import BaseActionTestCase


class MotionSetRecommendationActionTest(BaseActionTestCase):
    def test_reset_recommendation_correct(self) -> None:
        self.create_model("workflow/34", {})
        self.create_model("motion_state/66", {"motion_ids": [22], "workflow_id": 34})
        self.create_model(
            "motion_state/77", {"workflow_id": 34, "recommendation_label": "blablabal"},
        )
        self.create_model(
            "motion/22", {"meeting_id": 222, "state_id": 66},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.set_recommendation",
                    "data": [{"id": 22, "recommendation_id": 77}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("recommendation_id") == 77

    def test_reset_recommendation_missing_recommendation_label(self) -> None:
        self.create_model("workflow/34", {})
        self.create_model("motion_state/66", {"motion_ids": [22], "workflow_id": 34})
        self.create_model(
            "motion_state/77", {"workflow_id": 34},
        )
        self.create_model(
            "motion/22", {"meeting_id": 222, "state_id": 66},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.set_recommendation",
                    "data": [{"id": 22, "recommendation_id": 77}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Recommendation_label of a recommendation must be set." in str(
            response.data
        )

    def test_reset_recommendation_not_matching_workflow_ids(self) -> None:
        self.create_model("workflow/34", {})
        self.create_model("motion_state/66", {"motion_ids": [22], "workflow_id": 34})
        self.create_model(
            "motion_state/77",
            {"workflow_id": 123, "recommendation_label": "blablabal"},
        )
        self.create_model(
            "motion/22", {"meeting_id": 222, "state_id": 66},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.set_recommendation",
                    "data": [{"id": 22, "recommendation_id": 77}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "State is from a different workflow as motion." in str(response.data)
