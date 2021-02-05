from tests.system.action.base import BaseActionTestCase


class MotionChangeRecommendationActionTest(BaseActionTestCase):
    def test_create_good_required_fields(self) -> None:
        self.create_model("meeting/1", {"motion_ids": [233]})
        self.create_model(
            "motion/233",
            {"meeting_id": 1},
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
        assert model.get("type") == "replacement"
        assert model.get("meeting_id") == 1
        assert int(str(model.get("creation_time"))) > 1600246886

    def test_create_good_all_fields(self) -> None:
        self.create_model("meeting/1", {"motion_ids": [233]})
        self.create_model(
            "motion/233",
            {"meeting_id": 1},
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
                            "type": "replacement",
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
        assert model.get("type") == "replacement"
        assert model.get("other_description") == "other_description_iuDguxZp"
        assert model.get("meeting_id") == 1
        assert int(str(model.get("creation_time"))) > 1600246886

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/",
            json=[{"action": "motion_change_recommendation.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['line_from', 'line_to', 'text', 'motion_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.create_model("meeting/1", {"motion_ids": [233]})
        self.create_model(
            "motion/233",
            {"meeting_id": 1},
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
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_title_change_recommendation(self) -> None:
        self.create_model("meeting/1", {"motion_ids": [233]})
        self.create_model(
            "motion/233",
            {"meeting_id": 1},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_change_recommendation.create",
                    "data": [
                        {
                            "line_from": 0,
                            "line_to": 0,
                            "text": "new_title",
                            "motion_id": 233,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
