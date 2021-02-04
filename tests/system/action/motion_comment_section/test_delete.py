from tests.system.action.base import BaseActionTestCase


class MotionCommentSectionActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("motion_comment_section/111", {"name": "name_srtgb123"})
        response = self.client.post(
            "/",
            json=[{"action": "motion_comment_section.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_comment_section/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion_comment_section/112", {"name": "name_srtgb123"})
        response = self.client.post(
            "/",
            json=[{"action": "motion_comment_section.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_comment_section/112")

    def test_delete_existing_comments(self) -> None:
        self.create_model("motion_comment/79", {"motion_id": 17})
        self.create_model(
            "motion_comment_section/1141",
            {"comment_ids": [79]},
        )

        response = self.client.post(
            "/",
            json=[{"action": "motion_comment_section.delete", "data": [{"id": 1141}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_comment_section/1141")
        assert (
            'This section has still comments in motion "17". Please remove all comments before deletion.'
            in response.json.get("message", "")
        )
