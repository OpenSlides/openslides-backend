from tests.system.action.base import BaseActionTestCase


class TagActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model("tag/111", {"name": "name_srtgb123"})
        response = self.client.post(
            "/",
            json=[
                {"action": "tag.update", "data": [{"id": 111, "name": "name_Xcdfgee"}]}
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("tag/111")
        self.assertEqual(model.get("name"), "name_Xcdfgee")

    def test_update_wrong_id(self) -> None:
        self.create_model("tag/111", {"name": "name_srtgb123"})
        response = self.client.post(
            "/",
            json=[
                {"action": "tag.update", "data": [{"id": 112, "name": "name_Xcdfgee"}]}
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("tag/111")
        self.assertEqual(model.get("name"), "name_srtgb123")
