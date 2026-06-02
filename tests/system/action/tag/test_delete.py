from tests.system.action.base import BaseActionTestCase


class TagDeleteTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models({"tag/111": {"name": "name_srtgb123", "meeting_id": 1}})

    def test_delete_correct(self) -> None:
        response = self.request("tag.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("tag/111")

    def test_delete_wrong_id(self) -> None:
        response = self.request("tag.delete", {"id": 112})
        self.assert_status_code(response, 400)
        self.assert_model_exists("tag/111")

    def test_delete_correct_2(self) -> None:
        self.create_motion(1)
        self.set_models(
            {
                "agenda_item/222": {
                    "comment": "test_comment_ertgd590854398",
                    "tag_ids": [111],
                    "meeting_id": 1,
                    "content_object_id": "motion/1",
                },
            }
        )
        response = self.request("tag.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("tag/112")
        self.assert_model_exists(
            "agenda_item/222",
            {
                "id": 222,
                "comment": "test_comment_ertgd590854398",
                "tag_ids": None,
                "content_object_id": "motion/1",
            },
        )
