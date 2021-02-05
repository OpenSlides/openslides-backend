from tests.system.action.base import BaseActionTestCase


class TagDeleteTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("tag/111", {"name": "name_srtgb123"})
        response = self.request("tag.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("tag/112")

    def test_delete_wrong_id(self) -> None:
        self.create_model("tag/112", {"name": "name_srtgb123"})
        response = self.request("tag.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("tag/112")

    def test_delete_correct_2(self) -> None:
        self.set_models(
            {
                "tag/111": {"name": "name_srtgb123", "tagged_ids": ["topic/222"]},
                "topic/222": {"title": "test_title_ertgd590854398", "tag_ids": [111]},
            }
        )
        response = self.request("tag.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("tag/112")
        self.assert_model_exists(
            "topic/222",
            {
                "id": 222,
                "meta_deleted": False,
                "title": "test_title_ertgd590854398",
                "tag_ids": [],
            },
        )
