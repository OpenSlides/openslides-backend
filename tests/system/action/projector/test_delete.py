from tests.system.action.base import BaseActionTestCase


class ProjectorDelete(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("projector/111", {"name": "name_srtgb123"})
        response = self.request("projector.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("projector/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("projector/112", {"name": "name_srtgb123"})
        response = self.request("projector.delete", {"id": 111})
        self.assert_status_code(response, 400)
        model = self.get_model("projector/112")
        assert model.get("name") == "name_srtgb123"
