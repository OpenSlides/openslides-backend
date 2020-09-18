from tests.system.action.base import BaseActionTestCase


class MotionChangeRecommendationActionTest(BaseActionTestCase):
    def test_create_good_required_fields(self) -> None:
        self.create_model(
            "motion/233", {"title": "title_pheK0Ja3ai", "statute_paragraph_id": None},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_change_recommendation.create",
                    "data": [
                        {
                            "line_from": 125,
                            "line_to": 234,
                            "text": "text_DvLXGcdW",
                            "motion_id": 233,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_change_recommendation/1")
        assert model.get("line_from") == 125
        assert model.get("line_to") == 234
        assert model.get("text") == "text_DvLXGcdW"
        assert model.get("motion_id") == 233
        assert model.get("type") == 0
        assert int(str(model.get("creation_time"))) > 1600246886

    def test_create_good_all_fields(self) -> None:
        self.create_model(
            "motion/233", {"title": "title_pheK0Ja3ai", "statute_paragraph_id": None},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_change_recommendation.create",
                    "data": [
                        {
                            "line_from": 125,
                            "line_to": 234,
                            "text": "text_DvLXGcdW",
                            "motion_id": 233,
                            "rejected": False,
                            "internal": True,
                            "type": 0,
                            "other_description": "other_description_iuDguxZp",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_change_recommendation/1")
        assert model.get("line_from") == 125
        assert model.get("line_to") == 234
        assert model.get("text") == "text_DvLXGcdW"
        assert model.get("motion_id") == 233
        assert model.get("rejected") is False
        assert model.get("internal") is True
        assert model.get("type") == 0
        assert model.get("other_description") == "other_description_iuDguxZp"
        assert int(str(model.get("creation_time"))) > 1600246886

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "motion_change_recommendation.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'line_from\\', \\'line_to\\', \\'text\\', \\'motion_id\\'] properties",
            str(response.data),
        )

    def test_create_wrong_field(self) -> None:
        self.create_model(
            "motion/233", {"title": "title_pheK0Ja3ai", "statute_paragraph_id": None},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_change_recommendation.create",
                    "data": [
                        {
                            "line_from": 125,
                            "line_to": 234,
                            "text": "text_DvLXGcdW",
                            "motion_id": 233,
                            "wrong_field": "text_AefohteiF8",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must not contain {\\'wrong_field\\'} properties",
            str(response.data),
        )
