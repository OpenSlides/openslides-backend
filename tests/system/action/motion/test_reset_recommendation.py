import time

from tests.system.action.base import BaseActionTestCase


class MotionResetRecommendationActionTest(BaseActionTestCase):
    def test_reset_recommendation_correct(self) -> None:
        check_time = round(time.time())
        self.set_models(
            {
                "meeting/222": {"name": "name_SNLGsvIV"},
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

    def test_reset_recommendation_correct_empty_recommendation(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_SNLGsvIV"},
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
