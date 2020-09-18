from tests.system.action.base import BaseActionTestCase


class MotionBlockActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("motion_block/111", {"name": "name_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "motion_block.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_block/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion_block/112", {"name": "name_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "motion_block.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_block/112")

    def test_delete_correct_2(self) -> None:
        self.create_model(
            "motion_block/111",
            {
                "name": "name_srtgb123",
                "list_of_speakers_id": 222,
                "agenda_item_id": 333,
            },
        )
        self.create_model(
            "list_of_speakers/222",
            {"closed": False, "content_object_id": "motion_block/111"},
        )
        self.create_model(
            "agenda_item/333",
            {
                "comment": "test_comment_ewoirzewoirioewr",
                "content_object_id": "motion_block/111",
            },
        )
        response = self.client.post(
            "/", json=[{"action": "motion_block.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
