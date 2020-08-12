from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class AgendaItemSystemTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(get_fqid("topic/1"), {"name": "test"})
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
