from tests.system.action.base import BaseActionTestCase


class MotionCommentUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(
            "motion_comment/111", {"comment": "comment_srtgb123"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_comment.update",
                    "data": [{"id": 111, "comment": "comment_Xcdfgee"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_comment/111")
        assert model.get("comment") == "comment_Xcdfgee"

    def test_update_wrong_id(self) -> None:
        self.create_model(
            "motion_comment/111", {"comment": "comment_srtgb123"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_comment.update",
                    "data": [{"id": 112, "comment": "comment_Xcdfgee"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_comment/111")
        assert model.get("comment") == "comment_srtgb123"
