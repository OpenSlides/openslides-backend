from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class AgendaItemActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(get_fqid("topic/1"), {"name": "test"})
        self.create_model(get_fqid("topic/102"), {"name": "topic_kHemtGYY"})
        self.create_model(
            get_fqid("agenda_item/111"), {"item_number": 101, "duration": 600},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.update",
                    "data": [{"id": 111, "duration": 1200}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("agenda_item/111"))
        model = self.datastore.get(get_fqid("agenda_item/111"))
        assert model.get("duration") == 1200
