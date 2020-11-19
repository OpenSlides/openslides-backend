from tests.system.action.base import BaseActionTestCase


class MotionDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("meeting/98", {"motion_ids": [111]})
        self.create_model("motion/111", {"title": "title_srtgb123", "meeting_id": 98})
        response = self.client.post(
            "/",
            json=[{"action": "motion.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion/112", {"title": "title_srtgb123"})
        response = self.client.post(
            "/",
            json=[{"action": "motion.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion/112")

    def test_delete_correct_cascading(self) -> None:
        self.create_model("meeting/98", {"motion_ids": [111]})
        self.create_model(
            "motion/111",
            {
                "title": "title_srtgb123",
                "list_of_speakers_id": 222,
                "agenda_item_id": 333,
                "meeting_id": 98,
            },
        )
        self.create_model(
            "list_of_speakers/222",
            {"closed": False, "content_object_id": "motion/111"},
        )
        self.create_model(
            "agenda_item/333",
            {
                "comment": "test_comment_ewoirzewoirioewr",
                "content_object_id": "motion/111",
            },
        )
        response = self.client.post(
            "/",
            json=[{"action": "motion.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion/111")
        self.assert_model_deleted("agenda_item/333")
        self.assert_model_deleted("list_of_speakers/222")
