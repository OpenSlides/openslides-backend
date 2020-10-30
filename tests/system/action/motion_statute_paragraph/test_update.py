from tests.system.action.base import BaseActionTestCase


class MotionStatuteParagraphActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model("motion_statute_paragraph/111", {"title": "title_srtgb123"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_statute_paragraph.update",
                    "data": [
                        {"id": 111, "title": "title_Xcdfgee", "text": "text_blablabla"}
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_statute_paragraph/111")
        model = self.get_model("motion_statute_paragraph/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("text") == "text_blablabla"

    def test_update_wrong_id(self) -> None:
        self.create_model("motion_statute_paragraph/111", {"title": "title_srtgb123"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_statute_paragraph.update",
                    "data": [{"id": 112, "title": "title_Xcdfgee"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_statute_paragraph/111")
        assert model.get("title") == "title_srtgb123"
