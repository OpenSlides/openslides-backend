from tests.system.action.base import BaseActionTestCase


class TagDeleteTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("tag/111", {"name": "name_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "tag.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("tag/112")

    def test_delete_wrong_id(self) -> None:
        self.create_model("tag/112", {"name": "name_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "tag.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("tag/112")
