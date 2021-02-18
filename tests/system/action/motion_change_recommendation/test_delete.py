from tests.system.action.base import BaseActionTestCase


class MotionChangeRecommendationActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("motion_change_recommendation/111")
        response = self.request("motion_change_recommendation.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_change_recommendation/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion_change_recommendation/112")
        response = self.request("motion_change_recommendation.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_change_recommendation/112")
