from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class TopicSystemTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(get_fqid("meeting/1"), {"name": "test"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "topic.create",
                    "data": [{"meeting_id": 1, "title": "test"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("topic/1"))
        topic = self.datastore.get(get_fqid("topic/1"))
        self.assertEqual(topic.get("meeting_id"), 1)
        self.assertEqual(topic.get("agenda_item_id"), 1)
        self.assert_model_exists(get_fqid("agenda_item/1"))
        agenda_item = self.datastore.get(get_fqid("agenda_item/1"))
        self.assertEqual(agenda_item.get("meeting_id"), 1)
        self.assertEqual(agenda_item.get("content_object_id"), "topic/1")
