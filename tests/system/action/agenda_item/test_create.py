from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class AgendaItemSystemTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(get_fqid("topic/1"), {"name": "test"})
        self.create_model(get_fqid("meeting/1"), {"name": "test"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.create",
                    "data": [{"meeting_id": 1, "content_object_id": "topic/1"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("agenda_item/1"))

    def test_create_more_fields(self) -> None:
        self.create_model(get_fqid("topic/1"), {"name": "test"})
        self.create_model(get_fqid("meeting/1"), {"name": "test"})
        self.create_model(get_fqid("agenda_item/42"), {"comment": "test"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.create",
                    "data": [
                        {
                            "meeting_id": 1,
                            "content_object_id": "topic/1",
                            "comment": "test_comment_oiuoitesfd",
                            "type": 2,
                            "parent_id": 42,
                            "duration": 360,
                            # "weight": 0,
                            # "closed": False
                        }
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("agenda_item/43"))
        agenda_item = self.datastore.get(get_fqid("agenda_item/43"))
        self.assertEqual(agenda_item["comment"], "test_comment_oiuoitesfd")
        self.assertEqual(agenda_item["type"], 2)
        self.assertEqual(agenda_item["parent_id"], 42)
        self.assertEqual(agenda_item["duration"], 360)
        self.assertEqual(agenda_item["weight"], 0)
        self.assertFalse(agenda_item.get("closed"))
