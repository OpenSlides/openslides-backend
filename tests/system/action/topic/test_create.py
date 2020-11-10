import simplejson as json

from tests.system.action.base import BaseActionTestCase


class TopicSystemTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("topic/41", {})
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
        self.assert_model_exists("topic/42")
        topic = self.get_model("topic/42")
        self.assertEqual(topic.get("meeting_id"), 1)
        self.assertEqual(topic.get("agenda_item_id"), 1)
        self.assert_model_exists("agenda_item/1")
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 1)
        self.assertEqual(agenda_item.get("content_object_id"), "topic/42")
        self.assert_model_exists(
            "list_of_speakers/1", {"content_object_id": "topic/42"}
        )
        self.assert_model_exists(
            "list_of_speakers/1", {"content_object_id": "topic/42"}
        )
        r = json.loads(response.data)
        print(r)
        self.assertTrue(r["success"])
        self.assertEqual(r["message"], "Actions handled successfully")
        self.assertEqual(r["results"], [[{"id": 42}]])

    def test_create_multi(self) -> None:
        self.create_model("meeting/1", {"name": "test"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "topic.create",
                    "data": [
                        {"meeting_id": 1, "title": "test1"},
                        {"meeting_id": 1, "title": "test2"},
                    ],
                },
                {
                    "action": "topic.create",
                    "data": [
                        {"meeting_id": 1, "title": "test3"},
                        {"meeting_id": 1, "title": "test4"},
                    ],
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/1")
        self.assert_model_exists("topic/2")
        self.assert_model_exists("topic/3")
        self.assert_model_exists("topic/4")
        r = json.loads(response.data)
        self.assertEqual(r["results"], [[{"id": 1}, {"id": 2}], [{"id": 3}, {"id": 4}]])

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
        self.assertEqual(agenda_item["weight"], 10000)
