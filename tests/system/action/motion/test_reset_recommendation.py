from tests.system.action.base import BaseActionTestCase


class MotionResetRecommendationActionTest(BaseActionTestCase):
    def test_reset_recommendation_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_state/77",
            {"meeting_id": 222, "name": "test1", "motion_recommendation_ids": [22]},
        )
        self.create_model(
            "motion/22", {"meeting_id": 222, "title": "test1", "recommendation_id": 77}
        )
        response = self.client.post(
            "/", json=[{"action": "motion.reset_recommendation", "data": [{"id": 22}]}]
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("recommendation_id") is None

    def test_reset_recommendation_correct_empty_recommendation(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_state/77",
            {"meeting_id": 222, "name": "test1", "motion_recommendation_ids": [22]},
        )
        self.create_model(
            "motion/22",
            {"meeting_id": 222, "title": "test1", "recommendation_id": None},
        )
        response = self.client.post(
            "/", json=[{"action": "motion.reset_recommendation", "data": [{"id": 22}]}]
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("recommendation_id") is None

    def test_reset_recommendation_wrong(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_state/77",
            {"meeting_id": 222, "name": "test1", "motion_recommendation_ids": [22]},
        )
        self.create_model(
            "motion/23", {"meeting_id": 222, "title": "test1", "recommendation_id": 77}
        )
        response = self.client.post(
            "/", json=[{"action": "motion.reset_recommendation", "data": [{"id": 22}]}]
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("motion/22")
