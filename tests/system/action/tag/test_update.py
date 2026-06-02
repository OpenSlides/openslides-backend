from tests.system.action.base import BaseActionTestCase


class TagActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models({"tag/111": {"name": "name_srtgb123", "meeting_id": 1}})

    def test_update_correct(self) -> None:
        response = self.request("tag.update", {"id": 111, "name": "name_Xcdfgee"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("tag/111", {"name": "name_Xcdfgee"})

    def test_update_wrong_id(self) -> None:
        response = self.request("tag.update", {"id": 112, "name": "name_Xcdfgee"})
        self.assert_status_code(response, 400)
        self.assert_model_exists("tag/111", {"name": "name_srtgb123"})
