from tests.system.action.base import BaseActionTestCase


class TopicUpdateTest(BaseActionTestCase):
    def test_update_simple(self) -> None:
        self.create_model("meeting/1", {"name": "test"})
        self.create_model("topic/1", {"title": "test", "meeting_id": 1})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "topic.update",
                    "data": [{"id": 1, "title": "test2", "text": "text"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        topic = self.get_model("topic/1")
        self.assertEqual(topic.get("title"), "test2")
        self.assertEqual(topic.get("text"), "text")

    def test_update_tag_ids_add(self) -> None:
        self.create_model("meeting/1", {"name": "test"})
        self.create_model("topic/1", {"title": "test", "meeting_id": 1})
        self.create_model("tag/1", {"name": "tag", "meeting_id": 1})
        response = self.client.post(
            "/", json=[{"action": "topic.update", "data": [{"id": 1, "tag_ids": [1]}]}],
        )
        self.assert_status_code(response, 200)
        topic = self.get_model("topic/1")
        self.assertEqual(topic.get("tag_ids"), [1])

    def test_update_tag_ids_remove(self) -> None:
        self.test_update_tag_ids_add()
        response = self.client.post(
            "/", json=[{"action": "topic.update", "data": [{"id": 1, "tag_ids": []}]}],
        )
        self.assert_status_code(response, 200)
        topic = self.get_model("topic/1")
        self.assertEqual(topic.get("tag_ids"), [])

    def test_update_multiple_with_tag(self) -> None:
        self.create_model("meeting/1", {"name": "test"})
        self.create_model(
            "tag/1",
            {"name": "tag", "meeting_id": 1, "tagged_ids": ["topic/1", "topic/2"]},
        )
        self.create_model("topic/1", {"title": "test", "meeting_id": 1, "tag_ids": [1]})
        self.create_model("topic/2", {"title": "test", "meeting_id": 1, "tag_ids": [1]})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "topic.update",
                    "data": [{"id": 1, "tag_ids": []}, {"id": 2, "tag_ids": []}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        topic = self.get_model("topic/1")
        self.assertEqual(topic.get("tag_ids"), [])
        topic = self.get_model("topic/2")
        self.assertEqual(topic.get("tag_ids"), [])
        tag = self.get_model("tag/1")
        self.assertEqual(tag.get("tagged_ids"), [])
