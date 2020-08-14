from openslides_backend.shared.exceptions import DatabaseException
from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class AgendaItemActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(get_fqid("topic/1"), {"name": "test"})
        self.create_model(get_fqid("topic/102"), {"name": "topic_kHemtGYY"})
        self.create_model(
            get_fqid("agenda_item/111"),
            {"item_number": 101, "content_object_id": "topic/1"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.update",
                    "data": [{"id": 111, "content_object_id": "topic/102"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("agenda_item/111"))
        model = self.datastore.get(get_fqid("agenda_item/111"))
        assert model.get("content_object_id") == "topic/102"

    def test_update_wrong_id(self) -> None:
        self.create_model(get_fqid("topic/1"), {"name": "test"})
        self.create_model(get_fqid("topic/102"), {"name": "topic_kHemtGYY"})
        self.create_model(
            get_fqid("agenda_item/111"),
            {"item_number": 101, "content_object_id": "topic/1"},
        )
        with self.assertRaises(DatabaseException):
            self.client.post(
                "/",
                json=[
                    {
                        "action": "agenda_item.update",
                        "data": [{"id": 112, "content_object_id": "topic/102"}],
                    }
                ],
            )
        model = self.datastore.get(get_fqid("agenda_item/111"))
        assert model.get("content_object_id") == "topic/1"
