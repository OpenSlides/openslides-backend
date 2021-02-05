from tests.system.action.base import BaseActionTestCase


class MotionBlockActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model("motion_block/111", {"title": "title_srtgb123"})
        response = self.request(
            "motion_block.update", {"id": 111, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_block/111")
        model = self.get_model("motion_block/111")
        assert model.get("title") == "title_Xcdfgee"

    def test_update_wrong_id(self) -> None:
        self.create_model("motion_block/111", {"title": "title_srtgb123"})
        response = self.request(
            "motion_block.update", {"id": 112, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_block/111")
        assert model.get("title") == "title_srtgb123"
