from tests.system.action.base import BaseActionTestCase


class TopicDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("topic/1", {"list_of_speakers_id": 2})
        self.create_model("list_of_speakers/2", {"content_object_id": "topic/1"})
        response = self.client.post(
            "/", json=[{"action": "topic.delete", "data": [{"id": 1}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("topic/1")
        self.assert_model_deleted("list_of_speakers/2")

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
            "/", json=[{"action": "topic.delete", "data": [{"id": 1}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("topic/1")
        self.assert_model_deleted("list_of_speakers/1")
