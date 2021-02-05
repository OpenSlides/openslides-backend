import time

from tests.system.action.base import BaseActionTestCase


class MotionSetRecommendationActionTest(BaseActionTestCase):
    def test_set_recommendation_correct(self) -> None:
        check_time = round(time.time())
        self.create_model(
            "motion_workflow/34",
            {
                "meeting_id": 222,
            },
        )
        self.create_model(
            "motion_state/66",
            {"meeting_id": 222, "motion_ids": [22], "workflow_id": 34},
        )
        self.create_model(
            "motion_state/77",
            {"meeting_id": 222, "workflow_id": 34, "recommendation_label": "blablabal"},
        )
        self.create_model(
            "motion/22",
            {"meeting_id": 222, "state_id": 66},
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
        assert model.get("last_modified", 0) >= check_time

    def test_set_recommendation_missing_recommendation_label(self) -> None:
        self.create_model(
            "motion_workflow/34",
            {
                "meeting_id": 222,
            },
        )
        self.create_model(
            "motion_state/66",
            {"meeting_id": 222, "motion_ids": [22], "workflow_id": 34},
        )
        self.create_model(
            "motion_state/77",
            {"meeting_id": 222, "workflow_id": 34},
        )
        self.create_model(
            "motion/22",
            {"meeting_id": 222, "state_id": 66},
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
            response.json["message"]
        )

    def test_set_recommendation_not_matching_workflow_ids(self) -> None:
        self.create_model(
            "motion_workflow/34",
            {
                "meeting_id": 222,
            },
        )
        self.create_model(
            "motion_state/66",
            {"meeting_id": 222, "motion_ids": [22], "workflow_id": 34},
        )
        self.create_model(
            "motion_state/77",
            {
                "meeting_id": 222,
                "workflow_id": 123,
                "recommendation_label": "blablabal",
            },
        )
        self.create_model(
            "motion/22",
            {"meeting_id": 222, "state_id": 66},
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
        assert "State is from a different workflow as motion." in response.json.get(
            "message", ""
        )
