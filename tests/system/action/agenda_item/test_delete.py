from tests.system.action.base import BaseActionTestCase


class AgendaItemActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("agenda_item/111", {"name": "name_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "agenda_item.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("agenda_item/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("agenda_item/112", {"name": "name_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "agenda_item.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("agenda_item/112")
