from tests.system.action.base import BaseActionTestCase


class MotionChangeRecommendationActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models(
            {
                "motion/25": {
                    "title": "title_pheK0Ja3ai",
                    "statute_paragraph_id": None,
                },
                "motion_change_recommendation/111": {
                    "line_from": 11,
                    "line_to": 23,
                    "text": "text_LhmrbbwS",
                    "motion_id": 25,
                },
            }
        )
        response = self.request(
            "motion_change_recommendation.update",
            {
                "id": 111,
                "text": "text_zzTWoMte",
                "rejected": False,
                "internal": True,
                "type": "insertion",
                "other_description": "other_description_IClpabuM",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_change_recommendation/111")
        assert model.get("text") == "text_zzTWoMte"
        assert model.get("rejected") is False
        assert model.get("internal") is True
        assert model.get("type") == "insertion"
        assert model.get("other_description") == "other_description_IClpabuM"

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "motion/25": {
                    "title": "title_pheK0Ja3ai",
                    "statute_paragraph_id": None,
                },
                "motion_change_recommendation/111": {
                    "line_from": 11,
                    "line_to": 23,
                    "text": "text_LhmrbbwS",
                    "motion_id": 25,
                },
            }
        )
        response = self.request(
            "motion_change_recommendation.update", {"id": 112, "text": "text_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_change_recommendation/111")
        assert model.get("text") == "text_LhmrbbwS"
        assert model.get("line_from") == 11
        assert model.get("line_to") == 23
        assert model.get("motion_id") == 25
