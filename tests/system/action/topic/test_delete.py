from tests.system.action.base import BaseActionTestCase


class TopicDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("topic/111", {"title": "title_srtgb123"})
        response = self.client.post(
            "/",
            json=[{"action": "topic.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("topic/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("topic/112", {"title": "title_srtgb123"})
        response = self.client.post(
            "/",
            json=[{"action": "topic.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("topic/112")

    def test_delete_correct_cascading(self) -> None:
        self.create_model(
            "topic/111",
            {
                "title": "title_srtgb123",
                "list_of_speakers_id": 222,
                "agenda_item_id": 333,
            },
        )
        self.create_model(
            "list_of_speakers/222",
            {"closed": False, "content_object_id": "topic/111"},
        )
        self.create_model(
            "agenda_item/333",
            {
                "comment": "test_comment_ewoirzewoirioewr",
                "content_object_id": "topic/111",
            },
        )
        response = self.client.post(
            "/",
            json=[{"action": "topic.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("topic/111")
        self.assert_model_deleted("agenda_item/333")
        self.assert_model_deleted("list_of_speakers/222")

    def test_create_delete(self) -> None:
        self.create_model("meeting/1", {})
        response = self.client.post(
            "/",
            json=[
                {"action": "topic.create", "data": [{"meeting_id": 1, "title": "test"}]}
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/1")
        self.assert_model_exists("list_of_speakers/1")
        response = self.client.post(
            "/",
            json=[{"action": "topic.delete", "data": [{"id": 1}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("topic/1")
        self.assert_model_deleted("list_of_speakers/1")

    def test_delete_with_agenda_item_and_filled_los(self) -> None:
        self.create_model(
            "meeting/1",
            {
                "agenda_item_ids": [3, 14],
                "list_of_speakers_ids": [3],
                "topic_ids": [1],
                "speaker_ids": [1, 2],
            },
        )
        self.create_model(
            "topic/1", {"agenda_item_id": 3, "list_of_speakers_id": 3, "meeting_id": 1}
        )
        self.create_model(
            "agenda_item/3",
            {"content_object_id": "topic/1", "meeting_id": 1},
        )
        self.create_model(
            "list_of_speakers/3",
            {"content_object_id": "topic/1", "speaker_ids": [1, 2], "meeting_id": 1},
        )
        self.create_model(
            "speaker/1",
            {"list_of_speakers_id": 3, "user_id": 1, "meeting_id": 1},
        )
        self.create_model(
            "speaker/2",
            {"list_of_speakers_id": 3, "user_id": 2, "meeting_id": 1},
        )
        self.update_model("user/1", {"speaker_$1_ids": [1], "speaker_$_ids": ["1"]})
        self.create_model("user/2", {"speaker_$1_ids": [2], "speaker_$_ids": ["1"]})
        response = self.client.post(
            "/",
            json=[{"action": "topic.delete", "data": [{"id": 1}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("topic/1")
        self.assert_model_deleted("agenda_item/3")
        self.assert_model_deleted("list_of_speakers/3")
        self.assert_model_deleted("speaker/1")
        self.assert_model_deleted("speaker/2")
        user_1 = self.get_model("user/1")
        assert user_1.get("speaker_$1_ids") == []
        assert user_1.get("speaker_$_ids") == []
