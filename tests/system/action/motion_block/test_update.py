from tests.system.action.base import BaseActionTestCase


class MotionBlockActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/11": {},
                "motion_block/111": {"title": "title_srtgb123", "meeting_id": 11},
            }
        )
        response = self.request(
            "motion_block.update", {"id": 111, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_block/111")
        model = self.get_model("motion_block/111")
        assert model.get("title") == "title_Xcdfgee"

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/11": {},
                "motion_block/111": {"title": "title_srtgb123", "meeting_id": 11},
            }
        )
        response = self.request(
            "motion_block.update", {"id": 112, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_block/111")
        assert model.get("title") == "title_srtgb123"

    def test_permissions(self) -> None:
        self.base_permission_test(
            {
                "meeting/11": {},
                "motion_block/111": {"meeting_id": 11, "title": "title_srtgb123"},
            },
            "motion_block.update",
            {"id": 111, "title": "title_Xcdfgee"},
        )
