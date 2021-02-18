from tests.system.action.base import BaseActionTestCase


class MotionStatuteParagraphActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("meeting/42")
        response = self.request(
            "motion_statute_paragraph.create",
            {"meeting_id": 42, "title": "test_Xcdfgee", "text": "blablabla"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_statute_paragraph/1")
        model = self.get_model("motion_statute_paragraph/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("weight") == 10000
        assert model.get("text") == "blablabla"

    def test_create_empty_data(self) -> None:
        response = self.request("motion_statute_paragraph.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'title', 'text'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.create_model("meeting/42")
        response = self.request(
            "motion_statute_paragraph.create", {"wrong_field": "text_AefohteiF8"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'title', 'text'] properties",
            response.json["message"],
        )
