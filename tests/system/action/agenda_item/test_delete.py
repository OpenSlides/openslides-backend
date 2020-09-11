from openslides_backend.shared.exceptions import DatabaseException
from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class AgendaItemActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model(get_fqid("agenda_item/111"), {"name": "name_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "agenda_item.delete", "data": [{"id": 111}]}],
        )
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(DatabaseException):
            self.datastore.get(get_fqid("agenda_item/111"))

    def test_delete_wrong_id(self) -> None:
        self.create_model(get_fqid("agenda_item/112"), {"name": "name_srtgb123"})
        with self.assertRaises(DatabaseException):
            self.client.post(
                "/", json=[{"action": "agenda_item.delete", "data": [{"id": 111}]}],
            )
        self.assert_model_exists(get_fqid("agenda_item/112"))
