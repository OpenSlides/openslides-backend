from tests.system.action.base import BaseActionTestCase


class TopicSystemTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("meeting/1", {"name": "test"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "topic.create",
                    "data": [{"meeting_id": 1, "title": "test"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/1")
        topic = self.get_model("topic/1")
        self.assertEqual(topic.get("meeting_id"), 1)
        self.assertEqual(topic.get("agenda_item_id"), 1)
        self.assert_model_exists("agenda_item/1")
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 1)
        self.assertEqual(agenda_item.get("content_object_id"), "topic/1")
        self.assert_model_exists("list_of_speakers/1", {"content_object_id": "topic/1"})

    def test_create_more_fields(self) -> None:
        self.create_model("meeting/1", {"name": "test"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "topic.create",
                    "data": [
                        {
                            "meeting_id": 1,
                            "title": "test",
                            "agenda_type": 2,
                            "agenda_duration": 60,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/1")
        topic = self.get_model("topic/1")
        self.assertEqual(topic.get("meeting_id"), 1)
        self.assertEqual(topic.get("agenda_item_id"), 1)
        self.assertTrue(topic.get("agenda_type") is None)
        self.assert_model_exists("agenda_item/1")
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 1)
        self.assertEqual(agenda_item.get("content_object_id"), "topic/1")
        self.assertEqual(agenda_item["type"], 2)
        self.assertEqual(agenda_item["duration"], 60)
        self.assertEqual(agenda_item["weight"], 0)
