from tests.system.action.base import BaseActionTestCase


class ResourceDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("resource/111", {"token": "srtgb123"})
        response = self.request("resource.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("resource/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("resource/112", {"token": "srtgb123"})
        response = self.request("resource.delete", {"id": 111})
        self.assert_status_code(response, 400)
        model = self.get_model("resource/112")
        assert model.get("token") == "srtgb123"
