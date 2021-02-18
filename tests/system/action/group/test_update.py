from tests.system.action.base import BaseActionTestCase


class GroupUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(
            "group/111",
            {"name": "name_srtgb123"},
        )
        response = self.request("group.update", {"id": 111, "name": "name_Xcdfgee"})
        self.assert_status_code(response, 200)
        model = self.get_model("group/111")
        assert model.get("name") == "name_Xcdfgee"

    def test_update_wrong_id(self) -> None:
        self.create_model(
            "group/111",
            {"name": "name_srtgb123"},
        )
        response = self.request("group.update", {"id": 112, "name": "name_Xcdfgee"})
        self.assert_status_code(response, 400)
        model = self.get_model("group/111")
        assert model.get("name") == "name_srtgb123"
